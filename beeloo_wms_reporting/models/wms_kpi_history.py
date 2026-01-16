# -*- coding: utf-8 -*-
from odoo import models, fields, api

class BeelooWmsKpiHistory(models.Model):
    _name = 'beeloo.wms.kpi.history'
    _description = 'Histórico Diário de KPIs do Armazém'
    _order = 'date desc'

    date = fields.Date(string="Data", required=True, index=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Armazém", required=True)
    
    # Os totais calculados pelo "Motor"
    total_pallets_stored = fields.Integer(string="Total de Paletes Armazenados")
    total_footprints_occupied = fields.Float(string="Total de Posições-Chão Ocupadas")
    
    # O KPI principal que seu "Plano Mestre" pediu
    avg_stacking_factor = fields.Float(
        string="Fator de Empilhamento Real", 
        compute='_compute_avg_stacking_factor',
        store=True
    )
    
    # Campos que usamos no Pilar 0, para referência
    total_locations_capacity = fields.Float(string="Capacidade Total (Footprints)")
    standard_stacking_factor = fields.Float(string="Fator de Empilhamento Padrão")

    @api.depends('total_pallets_stored', 'total_footprints_occupied')
    def _compute_avg_stacking_factor(self):
        for record in self:
            if record.total_footprints_occupied > 0:
                record.avg_stacking_factor = record.total_pallets_stored / record.total_footprints_occupied
            else:
                record.avg_stacking_factor = 0.0