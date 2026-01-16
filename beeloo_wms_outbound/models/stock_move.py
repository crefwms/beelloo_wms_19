# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class StockMove(models.Model):
    _inherit = 'stock.move'

    # --------------------------------------------------------------------------
    # --- PLANO M (b4p-007) ---
    # --------------------------------------------------------------------------
    #
    # OBJETIVO: Desativar a lógica de FEFO/Auto-Seleção.
    #
    # ANÁLISE: O requisito do usuário não é FEFO automático
    # (order='lot_id.create_date ASC'), mas sim "Seleção Manual pelo Operador".
    #
    # O comportamento NATIVO do Odoo já faz a "Seleção Manual"
    # (ele cria a demanda, mas não pré-reserva um 'lot_id', forçando
    # o usuário a bipar no momento da validação).
    #
    # CONCLUSÃO: Nossa sobrescrita (override) abaixo estava
    # filosoficamente errada e tecnicamente quebrada (como visto no b4p-000).
    #
    # AÇÃO: Comentar a função inteira para restaurar o fluxo nativo.
    #
    # --------------------------------------------------------------------------

    # def _action_assign(self):
    #     """
    #     Sobrescrita para forçar a lógica FEFO (Primeiro que Vence, Primeiro que Sai)
    #     ou, neste caso, "Primeiro que Entrou" (baseado na data de criação do lote).
    #     """
    #     _logger.info("Beeloo WMS (Pilar 4): 'action_assign' interceptado para FEFO.")
        
    #     # --- ESTE CÓDIGO TODO ESTÁ DESATIVADO ---
    #
    #     # (Aqui existia a lógica que buscava 'stock.quant'
    #     # com 'order=lot_id.create_date ASC', que causava o
    #     # 'ValueError' e o comportamento indesejado de auto-seleção)
    #
    #     # (E também tentava criar 'stock.move.line' com 'qty_done: 0',
    #     # que também causava um 'ValueError')
    #
    #     # Ao comentar tudo, chamamos a função nativa (super):
    #     _logger.info("Beeloo WMS (Pilar 4): Função FEFO desativada. Usando 'super()' (Nativo Odoo).")
    #     return super(StockMove, self)._action_assign()
    
    pass # Deixamos o 'pass' para o arquivo Python ser válido se estiver vazio.