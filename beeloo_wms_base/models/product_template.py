from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # --- CAMPO CHAVE (Ponto 1) ---
    x_sku = fields.Integer(
        string='SKU (Agrupador)', 
        index=True,
        help="SKU Mestre. Usado para agrupar variantes fiscais (NFe) de um mesmo produto físico."
    )

    # --- Classificação HNK ---
    x_product_type = fields.Selection(
        selection=[
            ('pa', 'PA (Produto Acabado)'),
            ('insumo', 'Insumo'),
            ('rpm', 'RPM (Ativo de Giro)'),
        ],
        string='Tipo de Produto (Beeloo)'
    )
    
    # --- Dados Logísticos ---
    x_palletization_qty = fields.Integer(
        string='Paletização Padrão (Qtd)',
        help="Quantidade padrão de caixas/packs por palete. Ex: 91"
    )
    x_shelf_days = fields.Integer(
        string='Dias Shelf Life',
        help="Número de dias antes do vencimento para considerar o produto como expirado."
    )
    x_veto_days = fields.Integer(
        string='Dias Veto (CQ)',
        help="Número de dias para realizar o envio do produto para analise CQ."
    )
    x_max_stacking = fields.Integer(
        string='Empilhamento Máximo',
        help="Número máximo de paletes que podem ser empilhados."
    )
    x_pallet_type_id = fields.Many2one(
        comodel_name='product.product',
        string='Tipo de Palete Padrão',
        domain="[('x_product_type', '=', 'rpm'), ('categ_id', 'ilike', 'Palete')]", 
    )
    
    @api.onchange('x_product_type')
    def _onchange_x_product_type_set_tracking(self):
        """
        Garante que PAs, Insumos e RPMs sejam rastreados.
        """
        if self.x_product_type in ('pa', 'insumo', 'rpm'):
            # 'lot' = Rastreabilidade por Lote (Muitos produtos, um lote. Ex: Lote HNK)
            # 'serial' = Rastreabilidade por No. de Série (Um produto, um lote. Ex: Palete SAP)
            
            # Pergunta para você: A etiqueta EWM do SAP é por PALETE (serial) 
            # ou por LOTE DE PRODUÇÃO (lot)?
            
            # Vamos assumir que cada palete de PA tem um ID único (serial)
            if self.x_product_type == 'pa':
                self.tracking = 'serial' # Rastreabilidade por Palete (No. de Série)
            else:
            # E que Insumos/RPMs são rastreados por Lote (Ex: Lote LUS-IN-001)
                self.tracking = 'lot' # Rastreabilidade por Lote
        else:
            self.tracking = 'none' # Se não for, não rastreia