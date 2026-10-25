# -*- coding: utf-8 -*-
# models/conferencia_item.py

from odoo import models, fields

class ConferenciaItem(models.Model):
    _name = 'lusitana_logistics.conferencia_item'
    _description = 'Item de Conferência (Etiqueta Bipada)'
    _rec_name = 'barcode'

    operation_line_id = fields.Many2one('lusitana_logistics.operation_line', string='Linha de Operação', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Produto Conferido', required=True)
    barcode = fields.Char(string='Código da Etiqueta', required=True, index=True)

    _sql_constraints = [
        ('barcode_operation_uniq', 'unique(operation_line_id, barcode)', 'Esta etiqueta já foi bipada para esta operação!')
    ]