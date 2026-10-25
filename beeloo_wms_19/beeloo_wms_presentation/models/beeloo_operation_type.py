# -*- coding: utf-8 -*-
from odoo import models, fields

class BeelooOperationType(models.Model):
    _name = 'beeloo.operation.type'
    _description = 'Beeloo: Tipos de Operação Logística'

    name = fields.Char(string='Nome da Operação', required=True)
    direction = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound')
    ], string='Direção', required=True)
    code = fields.Char(string='Código Interno')