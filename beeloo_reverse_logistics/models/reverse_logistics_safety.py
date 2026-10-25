from odoo import models, fields, api

class ReverseLogisticsSafetyChecklist(models.Model):
    _name = 'reverse.logistics.safety.checklist'
    _description = 'Safety Operational Checklist'

    name = fields.Char(string='Checklist Name', required=True)
    active = fields.Boolean(default=True)
    
    # Safety Questions
    check_leakage = fields.Boolean(string='Check for Leaks', help='Ensure no fluids are leaking')
    check_battery = fields.Boolean(string='Check Battery Condition', help='Verify battery is not swollen or damaged')
    check_fragile = fields.Boolean(string='Fragile Handling', help='Ensure unit is handled as fragile if necessary')
    epi_required = fields.Selection([
        ('gloves', 'Gloves'),
        ('glasses', 'Safety Glasses'),
        ('both', 'Both'),
        ('none', 'None')
    ], string='PPE Required', default='none')

    instructions = fields.Text(string='Safety Instructions')

class ReverseLogisticsSafetyLog(models.Model):
    _name = 'reverse.logistics.safety.log'
    _description = 'Registro de Segurança'
    _rec_name = 'rma_id'

    rma_id = fields.Many2one('reverse.logistics.rma', string='RMA Reference', required=True, ondelete='cascade')
    checklist_id = fields.Many2one('reverse.logistics.safety.checklist', string='Safety Checklist', required=True)
    user_id = fields.Many2one('res.users', string='Inspector', default=lambda self: self.env.user)
    date_inspection = fields.Datetime(string='Inspection Date', default=fields.Datetime.now)
    
    is_safe = fields.Boolean(string='Is Safe to Process?', default=False)
    notes = fields.Text(string='Security Notes')
    
    # Captured results
    leak_ok = fields.Boolean(string='No leaks detected')
    battery_ok = fields.Boolean(string='Battery OK')
