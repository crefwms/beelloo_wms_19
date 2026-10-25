# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BeelooPresentationLacreLine(models.Model):
    _name = 'beeloo.presentation.lacre.line'
    _description = 'Beeloo: Linha de Lacre na Apresentação'

    presentation_id = fields.Many2one(
        'beeloo.presentation', 
        string='Apresentação', 
        required=True, 
        ondelete='cascade'
    )
    lacre_id = fields.Many2one(
        'beeloo.lacre', 
        string='Lacre HNK', 
        required=True, 
        domain="[('status', '=', 'disponivel')]",
        ondelete='restrict'
    )
    imagem_evidencia = fields.Image(string="Evidência (Foto)")

class BeelooPresentationImplementLine(models.Model):
    _name = 'beeloo.presentation.implement.line'
    _description = 'Beeloo: Linha de Implemento na Apresentação'
    _rec_name = 'implemento_id'

    presentation_id = fields.Many2one(
        'beeloo.presentation', 
        string='Apresentação de Veículo', 
        required=True, 
        ondelete='cascade'
    )
    implemento_id = fields.Many2one(
        'beeloo.vehicle', 
        string='Implemento', 
        required=True, 
        domain="[('tipo_frota', '=', 'implemento')]", 
        ondelete='restrict'
    )
    
    _sql_constraints = [
        ('implemento_unique_per_presentation', 'unique(presentation_id, implemento_id)', 
         'Este implemento já foi adicionado a esta apresentação!'),
    ]