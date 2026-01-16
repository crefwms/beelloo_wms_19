# -*- coding: utf-8 -*-
from odoo import models, fields

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    x_damage_report_id = fields.Many2one(
        'beeloo.damage.report', 
        string="Boletim de Avaria (Beeloo)",
        copy=False
    )