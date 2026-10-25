from odoo import models, fields, api

class ReverseLogisticsControlTower(models.Model):
    _name = 'reverse.logistics.control.tower'
    _description = 'Reverse Logistics Control Tower Dashboard'
    _auto = False # Sql view

    rma_id = fields.Many2one('reverse.logistics.rma', string='RMA', readonly=True)
    state = fields.Selection(related='rma_id.state', readonly=True)
    marketplace_type = fields.Selection(related='rma_id.marketplace_type', readonly=True)
    sla_status = fields.Selection(related='rma_id.sla_status', readonly=True)
    weight_divergence = fields.Float(related='rma_id.weight_divergence', readonly=True)

    def init(self):
        # This will be a database view for fast dashboard reporting
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW reverse_logistics_control_tower AS (
                SELECT 
                    id as id,
                    id as rma_id
                FROM reverse_logistics_rma
            )
        """)
