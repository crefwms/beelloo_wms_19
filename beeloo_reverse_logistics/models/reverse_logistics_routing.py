from odoo import models, fields, api

class ReverseLogisticsBatch(models.Model):
    _name = 'reverse.logistics.batch'
    _description = 'Reverse Collection Batch'
    _inherit = ['mail.thread']

    name = fields.Char(string='Batch Ref', required=True, copy=False, readonly=True, default='New')
    driver_id = fields.Many2one('res.partner', string='Driver/Carrier')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    
    rma_ids = fields.Many2many('reverse.logistics.rma', string='RMAs in Route')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_route', 'In Route'),
        ('completed', 'Completed')
    ], default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('reverse.logistics.batch') or 'New'
        return super(ReverseLogisticsBatch, self).create(vals)
