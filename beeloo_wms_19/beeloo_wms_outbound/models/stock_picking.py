from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_generate_traceability_report(self):
        """ Abre o Wizard de Relatório de Lastro """
        self.ensure_one()
        return {
            'name': '📋 Dados para NFe (Lastro)',
            'type': 'ir.actions.act_window',
            'res_model': 'beeloo.outbound.report',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }