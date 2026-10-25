from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class ReverseLogisticsRMA(models.Model):
    _name = 'reverse.logistics.rma'
    _description = 'Reverse Logistics RMA'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'marketplace_sla_deadline asc, id desc'

    name = fields.Char(string='RMA Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    sale_order_id = fields.Many2one('sale.order', string='Original Sale Order', required=True)
    partner_id = fields.Many2one('res.partner', related='sale_order_id.partner_id', store=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('authorized', 'Authorized'),
        ('collected', 'Collected'),
        ('received', 'Received at CD'),
        ('safety_check', 'Safety Inspection'),
        ('inspecting', 'Technical Triage'),
        ('grading', 'Grading'),
        ('finished', 'Finished'),
        ('rejected', 'Rejected/Fraud')
    ], string='Status', default='draft', tracking=True)

    # Marketplace & SLA
    marketplace_type = fields.Selection([
        ('magalu', 'Magalu'),
        ('ml', 'Mercado Livre'),
        ('amazon', 'Amazon'),
        ('direct', 'Direct Sale')
    ], string='Marketplace', required=True)
    
    marketplace_sla_deadline = fields.Datetime(string='SLA Deadline', tracking=True)
    sla_status = fields.Selection([
        ('normal', 'Normal'),
        ('warning', 'Warning'),
        ('overdue', 'Overdue')
    ], compute='_compute_sla_status', store=True)

    # Collection Data
    collection_type = fields.Selection([
        ('home', 'Home Collection'),
        ('dropoff', 'Drop-off Point'),
        ('pudo', 'PUDO / Hub')
    ], string='Collection Type')
    
    carrier_tracking_ref = fields.Char(string='Carrier Tracking')
    weight_declared = fields.Float(string='Declared Weight (kg)')
    weight_received = fields.Float(string='Received Weight (kg)')
    weight_divergence = fields.Float(string='Weight Divergence (%)', compute='_compute_weight_divergence')

    # Traceability & Loss Mitigation
    collector_id = fields.Many2one('res.users', string='Coletado por')
    receiver_id = fields.Many2one('res.users', string='Recebido por')
    triager_id = fields.Many2one('res.users', string='Triado por')
    grader_id = fields.Many2one('res.users', string='Grading por')
    
    collection_signature = fields.Binary(string='Assinatura do Cliente')
    date_collected = fields.Datetime(string='Data de Coleta')

    # Safety & Grading linked
    safety_log_ids = fields.One2many('reverse.logistics.safety.log', 'rma_id', string='Safety Logs')
    grading_ids = fields.One2many('reverse.logistics.grading.line', 'rma_id', string='Grading Lines')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('reverse.logistics.rma') or _('New')
        
        # Set default SLA based on marketplace
        if not vals.get('marketplace_sla_deadline'):
            days = 7 # Default
            if vals.get('marketplace_type') == 'magalu':
                days = 5
            elif vals.get('marketplace_type') == 'ml':
                days = 3
            vals['marketplace_sla_deadline'] = fields.Datetime.now() + timedelta(days=days)
            
        return super(ReverseLogisticsRMA, self).create(vals)

    @api.depends('marketplace_sla_deadline')
    def _compute_sla_status(self):
        now = fields.Datetime.now()
        for record in self:
            if not record.marketplace_sla_deadline:
                record.sla_status = 'normal'
                continue
            if now > record.marketplace_sla_deadline:
                record.sla_status = 'overdue'
            elif now > record.marketplace_sla_deadline - timedelta(hours=24):
                record.sla_status = 'warning'
            else:
                record.sla_status = 'normal'

    @api.depends('weight_declared', 'weight_received')
    def _compute_weight_divergence(self):
        for record in self:
            if record.weight_declared > 0:
                record.weight_divergence = abs(record.weight_received - record.weight_declared) / record.weight_declared * 100
            else:
                record.weight_divergence = 0.0
                
    def action_authorize(self):
        self.write({'state': 'authorized'})

    def action_collect(self):
        self.write({
            'state': 'collected',
            'collector_id': self.env.user.id,
            'date_collected': fields.Datetime.now()
        })

    def action_receive(self):
        self.write({
            'state': 'received',
            'receiver_id': self.env.user.id
        })

    def action_safety_start(self):
        self.write({
            'state': 'safety_check',
            'triager_id': self.env.user.id
        })

    def action_triage_start(self):
        # Already set triager_id in safety_start, but can update if different
        if not self.triager_id:
            self.triager_id = self.env.user.id
        self.write({'state': 'inspecting'})

    def action_grading_start(self):
        self.write({
            'state': 'grading',
            'grader_id': self.env.user.id
        })

    def action_finish(self):
        self.write({'state': 'finished'})

    def action_reject(self):
        self.write({'state': 'rejected'})
