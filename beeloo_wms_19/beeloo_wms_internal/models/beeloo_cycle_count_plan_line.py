# -*- coding: utf-8 -*-
from odoo import models, fields

class BeelooCycleCountPlanLine(models.Model):
    _name = 'beeloo.cycle.count.plan.line'
    _description = 'Linha do Plano de Contagem Cíclica'

    plan_id = fields.Many2one(
        'beeloo.cycle.count.plan', 
        string='Plano de Contagem', 
        ondelete='cascade', 
        required=True
    )
    product_id = fields.Many2one('product.product', string='Produto', readonly=True)
    location_id = fields.Many2one('stock.location', string='Localização', readonly=True)
    lot_id = fields.Many2one('stock.lot', string='Lote/No. Série', readonly=True)
    theoretical_qty = fields.Float(string='Qtd. Teórica (Odoo)', readonly=True)