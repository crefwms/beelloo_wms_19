# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Vehicle(models.Model):
    _name = 'beeloo.vehicle' # Renomeado
    _description = 'Cadastro de Veículos da Frota'

    name = fields.Char(string='Placa', required=True, index=True)
    transportadora_id = fields.Many2one('res.partner', string='Transportadora Proprietária',
                                        domain="[('category_id.name', '=', 'Transportadora')]")
    
    # Renomeando as referências dos modelos
    vehicle_type_id = fields.Many2one('beeloo.vehicle.type', string='Tipo de Veículo', required=True)
    body_type_id = fields.Many2one('beeloo.body.type', string='Tipo de Carroceria', required=True)
    tie_type_id = fields.Many2one('beeloo.tie.type', string='Tipo de Amarração')
    tightening_type_id = fields.Many2one('beeloo.tightening.type', string='Tipo de Aperto')
    
    tipo_frota = fields.Selection([
        ('tracao', 'Tração (Cavalo Mecânico, Truck)'),
        ('implemento', 'Implemento (Carreta, Baú, Sider)'),
        ('completo', 'Veículo Completo (Truck, VUC)')], 
        string='Tipo de Frota', required=True, default='completo')
    
    capacidade_paletes = fields.Integer(string='Capacidade de Paletes')
    tara = fields.Float(string='Tara (kg)')
    pbt = fields.Float(string='PBT - Peso Bruto Total (kg)')
    qtde_eixos = fields.Integer(string='Quantidade de Eixos', default=0)
    
    active = fields.Boolean(string='Ativo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "A placa do veículo já está cadastrada!")
    ]

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.upper().replace(' ', '')