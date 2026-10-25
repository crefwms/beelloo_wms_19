from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta

class OeaRequirementItem(models.Model):
    _name = 'oea.requirement.item'
    _description = 'OEA Requirement Item - Interaction & Evidence'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'requirement_id, sequence, id'

    name = fields.Char(string='Title', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    requirement_id = fields.Many2one(
        'oea.requirement', 
        string='Requirement', 
        required=True,
        ondelete='cascade',
        domain=[('active', '=', True)]
    )
    
    requirement_type = fields.Selection(related='requirement_id.type', readonly=True)
    requirement_modality = fields.Selection(related='requirement_id.modality', readonly=True)
    requirement_complexity = fields.Selection(related='requirement_id.complexity', readonly=True)
    requirement_reference = fields.Char(related='requirement_id.reference', readonly=True)
    requirement_category = fields.Char(related='requirement_id.category', readonly=True)
    
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('in_progress', 'Em Andamento'),
        ('pending_review', 'Pendente Revisão'),
        ('validated', 'Validado'),
        ('rejected', 'Rejeitado'),
        ('not_applicable', 'Não Aplicável'),
    ], string='Status', default='draft', tracking=True, required=True)
    
    performed_by = fields.Many2one('res.users', string='Responsável', tracking=True)
    performed_date = fields.Datetime(string='Data de Execução', tracking=True)
    due_date = fields.Date(string='Data Prevista')
    
    evidence_ids = fields.Many2many(
        'ir.attachment', 
        'oea_item_evidence_rel',
        'item_id',
        'attachment_id',
        string='Evidências'
    )
    
    notes = fields.Html(string='Observações')
    validation_notes = fields.Html(string='Notas de Validação')
    
    odoo_model_id = fields.Many2one(
        'ir.model',
        string='Modelo Odoo Vinculado',
        help='Modelo Odoo relacionado a esta evidência'
    )
    odoo_record_id = fields.Integer(string='Registro Odoo ID')
    odoo_record_ref = fields.Reference(
        string='Referência Odoo',
        selection='_selection_target_model',
        compute='_compute_odoo_record_ref',
        inverse='_inverse_odoo_record_ref'
    )
    
    parent_id = fields.Many2one(
        'oea.requirement.item',
        string='Item Pai',
        ondelete='cascade'
    )
    child_ids = fields.One2many('oea.requirement.item', 'parent_id', string='Sub-itens')
    
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )
    
    approver_id = fields.Many2one(
        'res.users',
        string='Aprovador',
        tracking=True,
        help='Usuário que aprovou o item'
    )
    approval_date = fields.Datetime(
        string='Data de Aprovação',
        tracking=True
    )
    approval_notes = fields.Html(string='Notas de Aprovação')
    
    audit_id = fields.Many2one(
        'oea.audit',
        string='Auditoria',
        help='Auditoria relacionada a este item'
    )
    
    active = fields.Boolean(default=True)

    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise UserError('Erro! Você não pode criar uma hierarquia recursiva (um item não pode ser pai de si mesmo).')

    @api.model
    def _selection_target_model(self):
        models = self.env['ir.model'].search([
            ('model', 'in', [
                'stock.picking', 'stock.lot', 'stock.quant',
                'hr.employee', 'hr.job', 'res.partner',
                'account.move', 'account.invoice',
                'documents.document', 'maintenance.equipment',
                'maintenance.request'
            ])
        ])
        return [(m.model, m.name) for m in models]

    @api.depends('odoo_model_id', 'odoo_record_id')
    def _compute_odoo_record_ref(self):
        for item in self:
            if item.odoo_model_id and item.odoo_record_id:
                item.odoo_record_ref = '%s,%d' % (item.odoo_model_id.model, item.odoo_record_id)
            else:
                item.odoo_record_ref = False

    def _inverse_odoo_record_ref(self):
        for item in self:
            if item.odoo_record_ref:
                item.odoo_model_id = self.env['ir.model'].search([('model', '=', item.odoo_record_ref._name)], limit=1)
                item.odoo_record_id = item.odoo_record_ref.id

    def action_start(self):
        self.write({
            'state': 'in_progress',
            'performed_by': self.env.user.id,
            'performed_date': fields.Datetime.now()
        })

    def action_pending_review(self):
        self.write({'state': 'pending_review'})
        self._send_notification()
        self._schedule_review_activity()

    def _schedule_review_activity(self):
        for item in self:
            item.activity_schedule(
                'oea_management.oea_activity_type_review',
                date_deadline=fields.Date.today() + timedelta(days=3),
                note=f'Revisar item pendente: {item.name}'
            )

    def action_validate(self):
        self.write({
            'state': 'validated',
            'performed_date': fields.Datetime.now(),
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

    def action_reject(self):
        self.write({'state': 'rejected', 'approver_id': False, 'approval_date': False})

    def action_reset(self):
        self.write({'state': 'draft'})

    def action_mark_na(self):
        self.write({'state': 'not_applicable'})

    def _send_notification(self):
        for item in self:
            item.message_post(
                body=f"<b>Item pendente de revisão:</b> {item.name}",
                message_type='notification',
                partner_ids=[item.requirement_id.create_uid.partner_id.id] if item.requirement_id.create_uid else []
            )

    @api.model
    def get_dashboard_data(self):
        Requirement = self.env['oea.requirement']
        Item = self.env['oea.requirement.item']
        
        total_reqs = Requirement.search_count([('active', '=', True)])
        
        items = Item.search([])
        total_items = len(items)
        
        validated = len(items.filtered(lambda i: i.state == 'validated'))
        in_progress = len(items.filtered(lambda i: i.state == 'in_progress'))
        pending = len(items.filtered(lambda i: i.state == 'pending_review'))
        rejected = len(items.filtered(lambda i: i.state == 'rejected'))
        draft = len(items.filtered(lambda i: i.state == 'draft'))
        na = len(items.filtered(lambda i: i.state == 'not_applicable'))
        
        progress = (validated / total_items * 100) if total_items > 0 else 0
        
        by_modality = {}
        for mod in ['compliance', 'security', 'both']:
            mod_items = items.filtered(lambda i: i.requirement_modality == mod)
            mod_total = len(mod_items)
            mod_validated = len(mod_items.filtered(lambda i: i.state == 'validated'))
            by_modality[mod] = {
                'total': mod_total,
                'validated': mod_validated,
                'progress': (mod_validated / mod_total * 100) if mod_total > 0 else 0
            }
        
        by_category = {}
        for cat in items.mapped('requirement_category'):
            if cat:
                cat_items = items.filtered(lambda i: i.requirement_category == cat)
                cat_total = len(cat_items)
                cat_validated = len(cat_items.filtered(lambda i: i.state == 'validated'))
                by_category[cat] = {
                    'total': cat_total,
                    'validated': cat_validated,
                    'progress': (cat_validated / cat_total * 100) if cat_total > 0 else 0
                }
        
        return {
            'total_requirements': total_reqs,
            'total_items': total_items,
            'validated': validated,
            'in_progress': in_progress,
            'pending': pending,
            'rejected': rejected,
            'draft': draft,
            'not_applicable': na,
            'progress': round(progress, 1),
            'by_modality': by_modality,
            'by_category': by_category,
        }

    def _cron_check_overdue_items(self):
        today = fields.Date.today()
        overdue_items = self.search([
            ('due_date', '<', today),
            ('state', 'not in', ['validated', 'not_applicable', 'rejected']),
            ('active', '=', True),
        ])
        
        for item in overdue_items:
            item.activity_schedule(
                'oea_management.oea_activity_type_overdue',
                date_deadline=today,
                note=f'Item de ação atrasado: {item.name}'
            )
        
        return True
