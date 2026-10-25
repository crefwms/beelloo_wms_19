# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class Lacre(models.Model):
    _name = 'beeloo.lacre' # Renomeado
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Controle de Lacres'
    _rec_name = 'name' 

    name = fields.Char(string='Número do Lacre', required=True, copy=False, index=True) 
    
    tipo_lacre = fields.Selection([
        ('hnk', 'Heineken (HNK)'),
        ('armador', 'Armador (Externo)'),
        ('outro', 'Outro'),
    ], string='Tipo de Lacre', required=True, default='hnk')

    status = fields.Selection([
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('utilizado', 'Utilizado'),
        ('danificado', 'Danificado'),
        ('perdido', 'Perdido'),
    ], string='Status', default='disponivel', required=True, tracking=True)

    fornecedor_id = fields.Many2one('res.partner', string='Fornecedor')
    data_recebimento = fields.Date(string='Data de Recebimento')

    data_atribuicao = fields.Datetime(string='Data de Atribuição', readonly=True) 
    user_atribuicao_id = fields.Many2one('res.users', string='Atribuído Por', readonly=True) 
    
    # Referência à Apresentação
    presentation_line_id = fields.One2many(
        'beeloo.presentation.lacre.line', # Modelo que você já tem
        'lacre_id', 
        string='Linha da Apresentação'
    )

    observacoes = fields.Text(string='Observações')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Este número de lacre já está cadastrado!")
    ]

    # ... (suas funções write e create portadas) ...