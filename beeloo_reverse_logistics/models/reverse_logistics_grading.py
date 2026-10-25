from odoo import models, fields, api

class ReverseLogisticsGradingLine(models.Model):
    _name = 'reverse.logistics.grading.line'
    _description = 'Technical Grading Line'

    rma_id = fields.Many2one('reverse.logistics.rma', string='RMA', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    
    grade = fields.Selection([
        ('a', 'A-Grade (Novo/Reintegração)'),
        ('b', 'B-Grade (Avaria leve/Outlet)'),
        ('c', 'C-Grade (Sucata/Descarte)')
    ], string='Final Grade', tracking=True)

    checklist_status = fields.Selection([
        ('ok', 'OK'),
        ('nok', 'Missing/Broken'),
        ('damage', 'Damaged')
    ], string='Condition')

    notes = fields.Text(string='Technical Notes')
    
    # Photos will be handled via mail.thread or dedicated attachment fields
    photo_ids = fields.Many2many('ir.attachment', string='Product Photos')

    def action_apply_grade(self):
        # Business logic for stock movement depending on grade will be added in stock_data logic
        pass
