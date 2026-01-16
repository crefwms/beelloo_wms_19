from odoo import models, fields

class StockLocation(models.Model):
    _inherit = 'stock.location'

    # --- CAMPO CHAVE (Ponto 3) ---
    x_footprint_capacity = fields.Integer(
        string="Capacidade (Footprints)",
        help="Número de posições-palete (footprints) que esta localização suporta no chão."
    )

    # --- Tipo de Armazenagem ---
    x_storage_type = fields.Selection(
        selection=[
            ('internal', 'Interno'),
            ('external', 'Externo')
        ], 
        string="Tipo de Armazenagem", 
        help="Classifica o endereço como área interna/coberta ou externa."
    )
    
    # --- KPI (Calculado via Cron) ---
    x_occupancy_percent = fields.Float(
        string='Taxa de Ocupação (%)',
        store=True, 
        readonly=True,
        help="Calculado automaticamente pela rotina de KPIs. Mostra o % de footprints ocupados."
    )