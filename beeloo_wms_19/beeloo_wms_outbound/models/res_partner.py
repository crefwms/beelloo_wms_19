# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    x_channel_type = fields.Selection([
        ('cda', 'CDA'), ('revenda', 'Revenda'), ('transferencia', 'Transferência'),
        ('as_atacado', 'AS Atacado'), ('as_varejo', 'AS Varejo'),
        ('multimarcas', 'Multimarcas'), ('outros', 'Outros'), ('auto', 'Auto Serviço'),
        ('distribuicao', 'Distribuidor'), ('fabrica', 'Fábrica'),
    ], string="Canal do Cliente")
    
    x_policy_type = fields.Selection([
        ('percentage', 'Percentual de Vida Consumida'),
        ('fixed_days', 'Dias Restantes Mínimos (Fixos)'),
    ], string="Tipo de Política Shelf Life", default='percentage')
    
    x_shelf_life_percent = fields.Float(string='% Máximo de Vida Consumida')
    x_fixed_days_value = fields.Integer(string="Dias Restantes Mínimos")

    # (A função name_get também é portada)
    def name_get(self):
        result = []
        for partner in self:
            name = partner.name
            if partner.ref:
                name = f"[{partner.ref}] {name}"
            result.append((partner.id, name))
        return result