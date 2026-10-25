from odoo import models, fields, api

class OeaAudit(models.Model):
    _name = 'oea.audit'
    _description = 'OEA Audit / Compliance Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Audit ID', required=True, copy=False, readonly=True, 
                      index=True, default=lambda self: 'New')
    company_id = fields.Many2one('res.company', string='Company', required=True, 
                                 default=lambda self: self.env.company)
    date = fields.Date(string='Audit Date', default=fields.Date.context_today)
    line_ids = fields.One2many('oea.audit.line', 'audit_id', string='Audit Lines')
    
    action_item_count = fields.Integer(string='Itens de Ação', compute='_compute_action_item_count')
    progress = fields.Float(string='Progress (%)', compute='_compute_progress', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('oea.audit') or 'OEA/' + fields.Date.today().strftime('%Y/%m/%d')
        return super().create(vals_list)

    @api.depends('line_ids.action_item_id.state')
    def _compute_progress(self):
        for audit in self:
            lines = audit.line_ids
            if not lines:
                audit.progress = 0
                continue
            # Progress based on validated action items
            validated_lines = lines.filtered(lambda l: l.action_item_id.state == 'validated' or l.action_item_id.state == 'not_applicable')
            audit.progress = (len(validated_lines) / len(lines)) * 100

    def _compute_action_item_count(self):
        for audit in self:
            audit.action_item_count = len(audit.line_ids.mapped('action_item_id'))

    def action_view_action_items(self):
        self.ensure_one()
        action_item_ids = self.line_ids.mapped('action_item_id').ids
        return {
            'name': 'Itens de Ação',
            'type': 'ir.actions.act_window',
            'res_model': 'oea.requirement.item',
            'view_mode': 'list,form',
            'domain': [('id', 'in', action_item_ids)],
            'context': {'default_audit_id': self.id},
            'target': 'current',
        }

    def action_generate_checklist(self):
        Item = self.env['oea.requirement.item']
        for audit in self:
            for line in audit.line_ids:
                if not line.action_item_id:
                    item = Item.create({
                        'name': line.requirement_id.name,
                        'requirement_id': line.requirement_id.id,
                        'company_id': audit.company_id.id,
                        'state': 'draft',
                    })
                    line.action_item_id = item.id
        
        # Return action to show the items
        action_item_ids = self.line_ids.mapped('action_item_id').ids
        return {
            'name': 'Itens de Ação Gerados',
            'type': 'ir.actions.act_window',
            'res_model': 'oea.requirement.item',
            'view_mode': 'list,form',
            'domain': [('id', 'in', action_item_ids)],
            'target': 'current',
        }

class OeaAuditLine(models.Model):
    _name = 'oea.audit.line'
    _description = 'OEA Audit Line'

    audit_id = fields.Many2one('oea.audit', string='Audit', ondelete='cascade')
    requirement_id = fields.Many2one('oea.requirement', string='Requirement', required=True)
    requirement_desc = fields.Html(related='requirement_id.description', readonly=True)
    
    action_item_id = fields.Many2one('oea.requirement.item', string='Item de Ação', ondelete='set null')
    status = fields.Selection(related='action_item_id.state', string='Status (Ação)', readonly=True)
    
    notes = fields.Text(string='Observations')
    evidence_attachment_ids = fields.Many2many('ir.attachment', string='Evidence Attachments')
