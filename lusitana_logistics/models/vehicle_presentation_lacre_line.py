# -*- coding: utf-8 -*-
# models/vehicle_presentation_lacre_line.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class VehiclePresentationLacreLine(models.Model):
    _name = 'lusitana_logistics.vehicle_presentation_lacre_line'
    _description = 'Linha de Lacre na Apresentação de Veículo'

    presentation_id = fields.Many2one('lusitana_logistics.vehicle_presentation', string='Apresentação', required=True, ondelete='cascade')
    
    lacre_id = fields.Many2one(
        'lusitana_logistics.lacre', 
        string='Lacre HNK', 
        required=True, 
        domain="[('status', '=', 'disponivel')]",
        ondelete='restrict'
    )

    imagem_evidencia = fields.Image(string="Evidência (Foto)")