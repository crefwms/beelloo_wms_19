# -*- coding: utf-8 -*-
# models/operation_type.py

from odoo import models, fields

class OperationType(models.Model):
    _name = 'lusitana_logistics.operation_type'
    _description = 'Tipos de Operação Logística (Configurável)'

    name = fields.Char(string='Nome da Operação', required=True)
    direction = fields.Selection([
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound')
    ], string='Direção', required=True)
    code = fields.Char(string='Código Interno', help="Um código técnico para esta operação, se necessário.")

    # Campos para definir o comportamento desta operação
    requires_cliente = fields.Boolean(string='Requer Cliente?', help="Marque se esta operação (ex: Venda) exige um cliente.")
    requires_origem = fields.Boolean(string='Requer Origem?', help="Marque se esta operação (ex: Recebimento) exige uma origem.")
    requires_destino = fields.Boolean(string='Requer Destino?', help="Marque se esta operação (ex: Venda) exige um destino.")