# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class StockLocation(models.Model):
    _inherit = 'stock.location'

    # Este é o campo "Dado Vivo" que seu plano mestre pediu.
    # O "Motor" vai preencher este campo toda noite.
    x_occupancy_percent = fields.Float(string="Taxa de Ocupação (%)", default=0.0)

    @api.model
    def run_daily_kpi_calculation(self):
        """
        Esta é a função "Motor" (O Calculador).
        É chamada pelo Cron Job (ir.cron) toda noite.

        Plano de Ação:
        1. Itera sobre cada Armazém (stock.warehouse).
        2. Itera sobre cada Localização Interna (stock.location) desse armazém.
        3. Calcula a ocupação (footprints) e paletes para CADA localização.
        4. Atualiza o "Dado Vivo" (x_occupancy_percent) da localização (Ação A).
        5. Agrega os totais do armazém.
        6. Salva o "Dado Histórico" (beeloo.wms.kpi.history) para o armazém (Ação B).
        """
        _logger.info("Iniciando o 'Motor' de Cálculo de KPIs do Beeloo WMS...")
        
        # 1. Itera sobre cada Armazém
        all_warehouses = self.env['stock.warehouse'].search([])
        KpiHistory = self.env['beeloo.wms.kpi.history']

        for wh in all_warehouses:
            _logger.info(f"Processando Armazém: {wh.name}")
            
            # Contadores para o "Dado Histórico" (Agregado do Armazém)
            wh_total_pallets_stored = 0.0
            wh_total_footprints_occupied = 0.0
            
            # 2. Itera sobre cada Localização Interna
            # (Apenas localizações que são filhas do "view_location_id" do armazém
            #  e que são do tipo 'internal')
            internal_locations = self.env['stock.location'].search([
                ('location_id', 'child_of', wh.view_location_id.id),
                ('usage', '=', 'internal'),
                ('x_footprint_capacity', '>', 0) # Otimização: Só calcula quem tem capacidade
            ])

            for loc in internal_locations:
                
                # Contadores para o "Dado Vivo" (Por Localização)
                loc_total_pallets = 0.0
                loc_total_footprints = 0.0
                
                # 3. Calcula a ocupação
                quants = self.env['stock.quant'].search([
                    ('location_id', '=', loc.id),
                    ('quantity', '>', 0)
                ])
                
                for quant in quants:
                    # Usamos 'product_tmpl_id' pois nossos campos (Pilar 0) estão lá
                    product_template = quant.product_id.product_tmpl_id
                    
                    pal_qty = product_template.x_palletization_qty
                    stack = product_template.x_max_stacking
                    
                    if pal_qty > 0 and stack > 0:
                        num_pallets = quant.quantity / pal_qty
                        loc_total_pallets += num_pallets
                        # Lógica do seu Plano Mestre: (Paletes / Empilhamento)
                        loc_total_footprints += (num_pallets / stack)
                    else:
                        # Se o produto não tiver dados, loga um aviso
                        _logger.warning(f"Produto {quant.product_id.name} (ID: {quant.product_id.id}) sem dados de paletização/empilhamento.")

                # 4. Atualiza o "Dado Vivo" (Ação A)
                # (loc.x_footprint_capacity vem do Pilar 0)
                if loc.x_footprint_capacity > 0:
                    occupancy = (loc_total_footprints / loc.x_footprint_capacity) * 100
                    # Escreve no banco a taxa de ocupação da "Rua A / Corredor 01"
                    loc.write({'x_occupancy_percent': occupancy})
                
                # 5. Agrega os totais do armazém
                wh_total_pallets_stored += loc_total_pallets
                wh_total_footprints_occupied += loc_total_footprints
            
            # 6. Salva o "Dado Histórico" (Ação B)
            if wh.view_location_id.id: # Garante que o armazém está configurado
                total_capacity = sum(internal_locations.mapped('x_footprint_capacity'))
                
                KpiHistory.create({
                    'date': fields.Date.today(),
                    'warehouse_id': wh.id,
                    'total_pallets_stored': int(wh_total_pallets_stored),
                    'total_footprints_occupied': wh_total_footprints_occupied,
                    'total_locations_capacity': total_capacity,
                    'standard_stacking_factor': wh.x_standard_stacking_factor # (Campo do Pilar 0)
                })
        
        _logger.info("...Cálculo de KPIs do Beeloo WMS concluído.")
        return True