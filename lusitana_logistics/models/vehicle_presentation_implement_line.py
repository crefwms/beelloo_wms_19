# -*- coding: utf-8 -*-
# models/vehicle_presentation_implement_line.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VehiclePresentationImplementLine(models.Model):
    _name = 'lusitana_logistics.vehicle_presentation_implement_line'
    _description = 'Linha de Implemento na Apresentação de Veículo'
    _rec_name = 'implemento_id'

    presentation_id = fields.Many2one('lusitana_logistics.vehicle_presentation', string='Apresentação de Veículo', required=True, ondelete='cascade')
    implemento_id = fields.Many2one('lusitana_logistics.vehicle', string='Implemento', required=True, domain="[('tipo_frota', '=', 'implemento')]", ondelete='restrict')
    qtde_eixos_implemento = fields.Integer(string='Eixos do Implemento', related='implemento_id.qtde_eixos', readonly=True, store=True)
    

    _sql_constraints = [
        ('implemento_unique_per_presentation', 'unique(presentation_id, implemento_id)', 'Este implemento já foi adicionado a esta apresentação!'),
    ]