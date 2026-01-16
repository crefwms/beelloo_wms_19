# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Campo Computado para exibir Paletes
    x_pallet_qty = fields.Float(
        string='Qtd (Paletes)',
        compute='_compute_pallet_qty',
        digits=(16, 2),
        help="Quantidade convertida em paletes baseada no cadastro do produto (Paletização)."
    )

    @api.depends('quantity', 'product_id.x_palletization_qty')
    def _compute_pallet_qty(self):
        for quant in self:
            # Evita divisão por zero
            if quant.product_id.x_palletization_qty > 0:
                quant.x_pallet_qty = quant.quantity / quant.product_id.x_palletization_qty
            else:
                quant.x_pallet_qty = 0.0