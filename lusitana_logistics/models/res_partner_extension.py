# -*- coding: utf-8 -*-
# models/res_partner_extension.py
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_motorist = fields.Boolean(string="É Motorista", default=False)
    is_location = fields.Boolean(string='É Localização (Estoque/Pátio)') # NOVO CAMPO
    cnh_number = fields.Char(string='Número da CNH')
    validade_integracao = fields.Date(string='Validade da Integração')
    cnh_category = fields.Selection([
        ('a', 'A'),
        ('b', 'B'),
        ('c', 'C'),
        ('d', 'D'),
        ('e', 'E'),
        ('ab', 'AB'),
        ('ac', 'AC'),
        ('ad', 'AD'),
        ('ae', 'AE'),
    ], string='Categoria CNH')
    cnh_expiration_date = fields.Date(string='Data de Vencimento da CNH')
    mopp_certificate = fields.Boolean(string='Certificado MOPP')
    mopp_expiration_date = fields.Date(string='Vencimento MOPP')