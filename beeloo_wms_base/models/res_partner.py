# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Campos do seu 'res_partner_extension.py'
    is_motorist = fields.Boolean(string="É Motorista", default=False)
    cnh_number = fields.Char(string='Número da CNH')
    validade_integracao = fields.Date(string='Validade da Integração')
    cnh_category = fields.Selection([
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D'), ('e', 'E'),
        ('ab', 'AB'), ('ac', 'AC'), ('ad', 'AD'), ('ae', 'AE'),
    ], string='Categoria CNH')
    cnh_expiration_date = fields.Date(string='Data de Vencimento da CNH')
    mopp_certificate = fields.Boolean(string='Certificado MOPP')
    mopp_expiration_date = fields.Date(string='Vencimento MOPP')

    # --- Nossos novos campos de Bloqueio (conforme sua solicitação) ---
    x_is_blocked = fields.Boolean(string="Motorista Bloqueado", default=False)
    x_block_reason = fields.Text(string="Motivo do Bloqueio")
    x_block_source = fields.Selection([
        ('lusitana', 'Bloqueio Interno (Lusitana)'),
        ('client', 'Bloqueio Cliente (HNK)')
    ], string="Origem do Bloqueio")