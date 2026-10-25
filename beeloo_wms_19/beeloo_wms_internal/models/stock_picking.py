# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_open_damage_wizard(self):
        """
        Esta função é chamada por um novo botão na tree view das 'stock.move.line'.
        Ela abre o wizard (pop-up) para reportar a avaria.
        """
        self.ensure_one() # Garante que estamos em um picking
        
        # Pega o ID da linha de movimento que foi clicada
        # O Odoo passa isso pelo 'context'
        move_line_id = self.env.context.get('active_id')
        if not move_line_id:
            return

        # Abre o Wizard, pré-preenchendo a linha de movimento
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reportar Avaria'),
            'res_model': 'beeloo.damage.report.wizard', # Nosso Wizard
            'view_mode': 'form',
            'target': 'new', # Abre como pop-up
            'context': {
                'default_move_line_id': move_line_id,
            }
        }