# -*- coding: utf-8 -*-
from odoo import models, fields

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    x_standard_stacking_factor = fields.Float(
        string="Fator de Empilhamento Padrão (Contratual)",
        default=2.39,
        digits=(12, 2)
    )
    x_contracted_footprint_internal = fields.Integer(
        string="Base Posições Contratadas (Interno)",
    )
    x_contracted_footprint_external = fields.Integer(
        string="Base Posições Contratadas (Externo)",
    )