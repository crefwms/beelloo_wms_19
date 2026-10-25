# -*- coding: utf-8 -*-
# models/vehicle.py

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Vehicle(models.Model):
    _name = 'lusitana_logistics.vehicle'
    _description = 'Cadastro de Veículos da Frota'

    name = fields.Char(string='Placa', required=True, index=True)
    transportadora_id = fields.Many2one('res.partner', string='Transportadora Proprietária',
                                        domain="[('is_company', '=', True)]") # Filtra para mostrar apenas empresas
    
    vehicle_type_id = fields.Many2one('lusitana_logistics.vehicle_type', string='Tipo de Veículo', required=True)
    body_type_id = fields.Many2one('lusitana_logistics.body_type', string='Tipo de Carroceria', required=True)
    tie_type_id = fields.Many2one('lusitana_logistics.tie_type', string='Tipo de Amarração')
    tightening_type_id = fields.Many2one('lusitana_logistics.tightening_type', string='Tipo de Aperto')
    tipo_frota = fields.Selection([
        ('tracao', 'Tração (Cavalo Mecânico, Truck)'),
        ('implemento', 'Implemento (Carreta, Baú, Sider)'),
        ('completo', 'Veículo Completo (Truck, VUC)')], 
        string='Tipo de Frota', required=True, default='completo', 
        help="Define se o veículo é de tração, um implemento ou um veículo completo.")
    
    capacidade_paletes = fields.Integer(string='Capacidade de Paletes')
    tara = fields.Float(string='Tara (kg)')
    pbt = fields.Float(string='PBT - Peso Bruto Total (kg)')
    qtde_eixos = fields.Integer(string='Quantidade de Eixos', default=0, help="Número de eixos do veículo.")
    
    active = fields.Boolean(string='Ativo', default=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "A placa do veículo já está cadastrada!")
    ]

    @api.onchange('name')
    def _onchange_name(self):
        if self.name:
            self.name = self.name.upper().replace(' ', '')