# -*- coding: utf-8 -*-
from odoo import fields, models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    x_presentation_id = fields.Many2one(
        'beeloo.presentation', 
        string='Apresentação (Portaria)',
        copy=False,
        readonly=True
    )

    # --- A SOLUÇÃO "STUB" (O "FANTASMA") ---
    # Adicionamos uma função "fantasma" no Pilar 1.
    # Isto é apenas para o validador XML "calar a boca"
    # durante a instalação do Pilar 1.
    def action_load_items_from_xml(self):
        # Esta função não faz NADA aqui.
        # A função REAL (com a lógica) está no Pilar 2,
        # e o Odoo (por herança) vai chamá-la.
        pass
    # ----------------------------------------