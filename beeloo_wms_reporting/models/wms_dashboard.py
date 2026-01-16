# -*- coding: utf-8 -*-
from odoo import models, fields, api

class WmsDashboard(models.Model):
    _name = 'beeloo.wms.dashboard'
    _description = 'WMS Dashboard (Modelo de Apresentação)'

    # Este campo 'name' é só para dar um título
    name = fields.Char(default="Dashboard de KPIs do Armazém")
    
    # --- KPIs em Tempo Real (lendo o último registro do histórico) ---
    # Usamos compute + search para buscar o dado mais recente
    
    latest_avg_stacking_factor = fields.Float(
        string="Fator de Empilhamento Real", 
        compute="_compute_latest_kpis",
        digits=(16, 2)
    )
    latest_total_pallets_stored = fields.Integer(
        string="Ocupação Real (Paletes)",
        compute="_compute_latest_kpis"
    )
    latest_standard_stacking_factor = fields.Float(
        string="Meta Contratual (Empilhamento)",
        compute="_compute_latest_kpis",
        digits=(16, 2)
    )

    def _compute_latest_kpis(self):
        """
        Este é o "Motor" da Vitrine. Ele busca o último registro 
        que o "Motor" (Cron Job) calculou.
        """
        # Busca o último registro de CADA armazém (futuro)
        # Por enquanto, vamos pegar o último registro geral
        latest_kpi = self.env['beeloo.wms.kpi.history'].search(
            [], order='date desc', limit=1
        )
        
        for record in self:
            if latest_kpi:
                record.latest_avg_stacking_factor = latest_kpi.avg_stacking_factor
                record.latest_total_pallets_stored = latest_kpi.total_pallets_stored
                record.latest_standard_stacking_factor = latest_kpi.standard_stacking_factor
            else:
                record.latest_avg_stacking_factor = 0.0
                record.latest_total_pallets_stored = 0
                record.latest_standard_stacking_factor = 0.0

    # --- Gráficos (lendo TODOS os registros do histórico) ---
    
    kpi_history_ids = fields.One2many(
        'beeloo.wms.kpi.history',
        compute="_get_all_kpi_history" # Usamos um compute para preencher
    )

    def _get_all_kpi_history(self):
        # Encontra todos os registros de histórico
        all_history = self.env['beeloo.wms.kpi.history'].search([], order='date asc')
        for record in self:
            record.kpi_history_ids = all_history