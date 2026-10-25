# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockPutawayRule(models.Model):
    _inherit = 'stock.putaway.rule'

    # 1. Adicionamos nossos campos de "filtro"
    # (Estes campos vêm do 'beeloo_wms_base')
    x_product_type = fields.Selection(
        related='product_id.x_product_type', 
        readonly=True
    )
    
    # 2. Vamos criar um filtro pelo TIPO de armazenagem (Interno/Externo)
    x_storage_type = fields.Selection(
        selection=[
            ('internal', 'Interno'),
            ('external', 'Externo (Pátio)')
        ], 
        string="Tipo de Armazenagem de Destino",
        help="A regra SÓ se aplica se a localização de destino tiver este tipo."
    )
    
    # 3. Sobrescrevemos a função que procura a localização
    # Esta é a função mais importante do endereçamento
    
    def _get_putaway_location(self, product, quantity, package=None, packaging=None, **kwargs):
        # Esta função é chamada pelo Odoo para encontrar o local de destino
        
        # 1. Deixa o Odoo encontrar os locais padrão primeiro
        location = super()._get_putaway_location(product, quantity, package, packaging, **kwargs)
        
        # 2. Se a nossa regra (self) tiver um 'x_storage_type' definido...
        if self.x_storage_type:
            # ... e a localização que o Odoo encontrou (location)...
            # ... NÃO bate com o tipo que queremos...
            if location.x_storage_type != self.x_storage_type:
                # ... então descarta a sugestão do Odoo.
                return self.env['stock.location'] # Retorna vazio
        
        # 3. Se passou no filtro, retorna a localização sugerida.
        return location