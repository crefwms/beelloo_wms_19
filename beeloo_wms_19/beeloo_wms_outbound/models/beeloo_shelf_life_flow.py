# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import date, timedelta

class BeelooShelfLifeFlow(models.Model):
    _name = 'beeloo.shelf.life.flow'
    _description = 'Beeloo: Controle de Flow (Exceção de Shelf Life)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'beeloo.shelf.life.mixin'] # <<< Herdando o Mixin!
    _order = 'create_date desc'

    name = fields.Char(string="Chamado", readonly=True, required=True, copy=False, default=lambda self: _('Novo'))
    
    # --- A MUDANÇA PRINCIPAL ---
    # Substituímos 'snapshot.line' pelo estoque real do Odoo
    quant_id = fields.Many2one(
        'stock.quant', 
        string="Posição de Estoque (Quant)", 
        readonly=True
    )
    
    # O cliente para quem estamos pedindo a exceção
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    
    # Campos 'related' para facilitar a visualização
    product_id = fields.Many2one(
        'product.product', 
        string='Produto', 
        related='quant_id.product_id', 
        store=True
    )
    location_id = fields.Many2one(
        'stock.location', 
        string='Localização', 
        related='quant_id.location_id', 
        store=True
    )
    lot_id = fields.Many2one(
        'stock.lot', 
        string='Lote/No. Série', 
        related='quant_id.lot_id', 
        store=True
    )
    
    dt_number = fields.Char(string="Número da DT (Referência)")
    
    # Data do lote que estamos oferecendo (vem do 'stock.lot' que criamos no Pilar 2)
    offered_date = fields.Datetime(
        related='lot_id.create_date', # (ou qualquer que seja o caminho para o create_date)
        string="Data Ofertada"
    )
    
    # Data limite que o cliente aceitaria
    required_date = fields.Date(
        string="Data Necessária (Limite Aceitável)", 
        compute='_compute_required_date', 
        store=True
    )
    
    status = fields.Selection([
        ('draft', 'Rascunho'),
        ('sent', 'Pendente HNK'),
        ('approved', 'Aprovado (Exceção)'),
        ('rejected', 'Rejeitado'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    notes = fields.Text(string="Observações e Justificativa")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Novo')) == _('Novo'):
                # Usando a sequence que definimos no manifest
                vals['name'] = self.env['ir.sequence'].next_by_code('beeloo.shelf.life.flow') or _('Novo')
        return super().create(vals_list)

    @api.depends('partner_id', 'quant_id.product_id')
    def _compute_required_date(self):
        """
        Calcula a data de produção/recebimento "limite" que o cliente aceitaria.
        Usa a mesma lógica do Mixin.
        """
        today = fields.Date.today()
        for flow in self:
            if not flow.partner_id or not flow.product_id:
                flow.required_date = False
                continue
            
            # Usa a função do Mixin (que herdamos no _inherit)
            max_age_days = self._get_max_age_days(flow.product_id, flow.partner_id)
            
            if max_age_days is not None:
                # A data limite é Hoje - Idade Máxima Permitida
                flow.required_date = today - timedelta(days=int(max_age_days))
            else:
                flow.required_date = False # Nenhuma regra, aceita qualquer data