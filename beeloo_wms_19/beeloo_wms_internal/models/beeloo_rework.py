# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BeelooRework(models.Model):
    _name = 'beeloo.rework'
    _description = 'Controle de Avarias e Retrabalho'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Referência', required=True, copy=False, readonly=True, 
                       default=lambda self: _('Novo'))

    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('done', 'Concluído'),
        ('cancel', 'Cancelado')
    ], string='Status', default='draft', tracking=True)

    product_id = fields.Many2one(
        'product.product', 
        string='Produto a ser Retrabalhado (PA)', 
        required=True
    )
    product_qty = fields.Float(string='Quantidade a Retrabalhar', default=1.0)
    
    # O Lote/No. Série do produto avariado
    lot_id = fields.Many2one(
        'stock.lot', 
        string='Lote/No. de Série (Palete)',
        domain="[('product_id', '=', product_id)]",
        required=True
    )
    
    location_id = fields.Many2one(
        'stock.location', 
        string='Localização da Avaria',
        help="De onde o produto avariado está saindo."
    )
    
    # Campo para o operador dizer o que aconteceu
    reason = fields.Text(string='Motivo da Avaria')

    # A "Ordem de Desmontagem" do Odoo
    unbuild_order_id = fields.Many2one(
        'mrp.unbuild', 
        string='Ordem de Desmontagem', 
        readonly=True, 
        copy=False
    )
    
    # --- Lógica da Sequência ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Novo')) == _('Novo'):
                # (Aqui criaríamos uma Sequência 'beeloo.rework')
                vals['name'] = self.env['ir.sequence'].next_by_code('beeloo.rework') or _('Novo')
        return super().create(vals_list)

    # --- AÇÃO PRINCIPAL ---
    def action_confirm_rework(self):
        self.ensure_one()
        if not self.product_id.bom_ids:
            raise UserError(_("Este produto não possui uma Lista de Materiais (BoM) para 'desmontar'. Não é possível retrabalhar."))

        # 1. Encontra a BoM (Lista de Materiais) do produto
        bom = self.product_id.bom_ids[0] # Pega a primeira BoM
        
        # 2. Cria a Ordem de Desmontagem (Unbuild Order)
        unbuild_order = self.env['mrp.unbuild'].create({
            'product_id': self.product_id.id,
            'bom_id': bom.id,
            'product_qty': self.product_qty,
            'lot_id': self.lot_id.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.location_id.id, # Os componentes voltam para o mesmo local
            'origin': self.name,
        })
        
        # 3. Processa a Ordem de Desmontagem
        unbuild_order.action_unbuild()
        
        self.write({
            'unbuild_order_id': unbuild_order.id,
            'state': 'done'
        })
        
        # 4. O operador agora precisa dizer o que fazer com os componentes
        # (ex: dar baixa no líquido, manter a garrafa)
        # O Odoo já fez o movimento de estoque.
        # Agora o operador pode ir no 'unbuild_order' e dar baixa (scrap)
        # nos componentes que foram perdidos.
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.unbuild',
            'res_id': unbuild_order.id,
            'view_mode': 'form',
            'target': 'current',
        }