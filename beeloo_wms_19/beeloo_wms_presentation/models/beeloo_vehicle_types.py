# -*- coding: utf-8 -*-
from odoo import models, fields

class BeelooVehicleType(models.Model):
    _name = 'beeloo.vehicle.type'
    _description = 'Beeloo: Tipo de Veículo (Ex: Truck, Carreta)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')

class BeelooBodyType(models.Model):
    _name = 'beeloo.body.type'
    _description = 'Beeloo: Tipo de Carroceria (Ex: Sider, Baú)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')

class BeelooTieType(models.Model):
    _name = 'beeloo.tie.type'
    _description = 'Beeloo: Tipo de Amarração (Ex: Asa-delta)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')

class BeelooTighteningType(models.Model):
    _name = 'beeloo.tightening.type'
    _description = 'Beeloo: Tipo de Aperto (Ex: Catraca)'

    name = fields.Char(string='Nome', required=True)
    description = fields.Text(string='Descrição')