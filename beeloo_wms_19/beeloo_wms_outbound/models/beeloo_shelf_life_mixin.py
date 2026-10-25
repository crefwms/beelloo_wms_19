# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import date, timedelta

class BeelooShelfLifeMixin(models.AbstractModel):
    _name = 'beeloo.shelf.life.mixin'  # <--- TEM QUE SER EXATAMENTE ESSE NOME
    _description = 'Beeloo Shelf Life Mixin'

    @api.model
    def _get_max_age_days(self, product, partner):
        """
        Portado do seu 'ShelfLifeQueryWizard._get_max_age_days_for_line'.
        Calcula a "idade máxima" (em dias) que um lote pode ter.
        """
        # 'x_shelf_days' (do beeloo_wms_base) é a nossa "Vida Útil Total"
        total_life = product.product_tmpl_id.x_shelf_days 
        
        if not partner: # Se não houver cliente (ex: transferência interna)
            return None # Sem regras
            
        channel = partner.x_channel_type
        
        if not total_life > 0:
            return None # Produto não perecível

        # REGRA 1: Heineken (Sua lógica HNK)
        if channel in ('cda', 'revenda') and total_life == 60:
            return total_life - 30.0 # 30 dias restantes = 30 dias de idade máxima
        if channel == 'cda' and total_life > 60:
            return total_life - 60.0 # 60 dias restantes

        # REGRA 2: Dias Fixos (do res.partner)
        if partner.x_policy_type == 'fixed_days' and partner.x_fixed_days_value > 0:
            return total_life - partner.x_fixed_days_value

        # REGRA 3: Percentual (do res.partner)
        if partner.x_policy_type == 'percentage':
            policy_fraction = (partner.x_shelf_life_percent or 100.0) / 100.0
            return total_life * policy_fraction
            
        return None # Nenhuma regra se aplica