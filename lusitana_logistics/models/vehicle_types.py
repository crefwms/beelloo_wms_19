# -*- coding: utf-8 -*-
# models/vehicle_types.py

from odoo import models, fields

class VehicleType(models.Model):
    _name = 'lusitana_logistics.vehicle_type'
    _description = 'Tipo de Veículo (Ex: Truck, Carreta)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')
    qtde_padrao_lacres = fields.Integer(string='Qtde. Padrão de Lacres', help="Quantidade de lacres sugerida para este tipo de veículo.")

class BodyType(models.Model):
    _name = 'lusitana_logistics.body_type'
    _description = 'Tipo de Carroceria (Ex: Sider, Baú)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')
    is_container_type = fields.Boolean(string="É um Tipo de Contêiner?", help="Marque esta opção se esta carroceria for um contêiner, para acionar validações específicas.")

class TieType(models.Model):
    _name = 'lusitana_logistics.tie_type'
    _description = 'Tipo de Amarração (Ex: Asa-delta, Cantoneira)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')

class TighteningType(models.Model):
    _name = 'lusitana_logistics.tightening_type'
    _description = 'Tipo de Aperto (Ex: Catraca, Manivela)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')