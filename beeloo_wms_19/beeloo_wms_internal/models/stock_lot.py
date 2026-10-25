# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.date_utils import relativedelta
import logging

_logger = logging.getLogger(__name__)

class StockLot(models.Model):
    _inherit = 'stock.lot'

    def run_daily_veto_check(self):
        """
        Esta função é chamada pelo Cron Job.
        Ela varre todos os lotes, encontra os que estão "vetados"
        e os move para a quarentena.
        """
        _logger.info("Iniciando verificação de Veto (Quarentena) Beeloo...")
        
        # 1. Encontrar o Tipo de Operação de Quarentena (Mov. Interna)
        # Precisamos que o usuário configure isso.
        quarantine_picking_type = self.env['stock.picking.type'].search([
            ('x_is_quarantine_type', '=', True) # Novo campo!
        ], limit=1)
        
        if not quarantine_picking_type:
            _logger.warning("Beeloo Veto: Nenhum Tipo de Operação de Quarentena configurado (x_is_quarantine_type=True). Pulando.")
            return

        quarantine_location = quarantine_picking_type.default_location_dest_id
        if not quarantine_location:
            _logger.warning(f"Beeloo Veto: A Operação {quarantine_picking_type.name} não tem um local de destino padrão.")
            return

        # 2. Encontrar todos os lotes que precisam ser movidos
        today = fields.Date.context_today(self)
        
        # Busca por lotes que tenham 'x_veto_days' configurado no produto
        # e que estejam em uma localização de estoque padrão
        lots_to_check = self.env['stock.lot'].search([
            ('product_id.x_veto_days', '>', 0),
            ('quant_ids.location_id.usage', '=', 'internal')
        ])
        
        lots_to_move = self.env['stock.lot']
        for lot in lots_to_check:
            veto_days = lot.product_id.x_veto_days
            # 'create_date' é a data de recebimento do lote
            veto_date = lot.create_date.date() + relativedelta(days=veto_days)
            
            if veto_date <= today:
                # Este lote está vetado. Adiciona na lista.
                lots_to_move += lot
                
        if not lots_to_move:
            _logger.info("Beeloo Veto: Nenhum lote para mover hoje.")
            return

        # 3. Criar UM `stock.picking` para mover todos os lotes vetados
        picking = self.env['stock.picking'].create({
            'picking_type_id': quarantine_picking_type.id,
            'location_id': quarantine_picking_type.default_location_src_id.id, # Localização pai (Ex: /Estoque)
            'location_dest_id': quarantine_location.id, # Ex: /Estoque/Quarentena
            'origin': f"Veto Automático CQ - {today.isoformat()}",
        })
        
        # 4. Criar as 'stock.move.line' para CADA lote
        move_line_model = self.env['stock.move.line']
        for lot in lots_to_move:
            # Encontra o 'quant' (o estoque físico) daquele lote
            quant = lot.quant_ids.filtered(lambda q: q.quantity > 0 and q.location_id.usage == 'internal')
            if not quant:
                continue
            
            quant = quant[0] # Pega o primeiro 'quant'
            
            move_line_model.create({
                'picking_id': picking.id,
                'product_id': lot.product_id.id,
                'qty_done': quant.quantity,
                'product_uom_id': lot.product_id.uom_id.id,
                'lot_id': lot.id,
                'location_id': quant.location_id.id, # De onde está saindo
                'location_dest_id': quarantine_location.id, # Para onde vai
            })

        # 5. Valida a movimentação
        picking.action_confirm()
        picking.action_assign()
        picking.button_validate()
        
        _logger.info(f"Beeloo Veto: Movimentação {picking.name} criada para {len(lots_to_move)} lotes.")
        return True