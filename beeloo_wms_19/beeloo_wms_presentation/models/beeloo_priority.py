# -*- coding: utf-8 -*-
from odoo import models, fields

class BeelooPriority(models.Model):
    _name = 'beeloo.priority'
    _description = 'Beeloo: Cadastro de Prioridade de Carregamento'
    _order = 'sequence, name'

    name = fields.Char(string='Nome da Prioridade', required=True)
    sap_code = fields.Char(string='Código SAP', required=True, index=True)
    sequence = fields.Integer(string='Sequência', default=10)
    urgency_level = fields.Selection([
        ('0', '0 - Crítica / Imediata'),
        ('1', '1 - Alta'),
        ('2', '2 - Média'),
        ('3', '3 - Baixa'),
    ], string="Nível de Urgência", default='3', required=True)
    direction = fields.Selection([
        ('inbound', 'Entrada/Inbound'), 
        ('outbound', 'Saída/Outbound'),
        ('both', 'Ambos')
    ], string="Sentido da Operação", default='both', required=True)
    
    _sql_constraints = [
        ('sap_code_uniq', 'unique(sap_code)', 'Este código SAP já está cadastrado!')
    ]