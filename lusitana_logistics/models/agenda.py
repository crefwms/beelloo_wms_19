# -*- coding: utf-8 -*-
# models/agenda.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AgendaHeineken(models.Model):
    _name = 'lusitana_logistics.agenda_heineken'
    _description = 'Agenda de Carregamento Importada (SAP ZRTMFB012)'
    _rec_name = 'dt_documento'

    dt_documento = fields.Char(string='DT (Doc. Transporte)', required=True, index=True)
    
    transportadora_id = fields.Many2one(
        'res.partner', 
        string='Transportadora', 
        domain="[('category_id', 'ilike', 'Transportadora')]"
    )
    
    direction = fields.Selection(
        [
            ('inbound', 'Entrada/Inbound'), 
            ('outbound', 'Saída/Outbound')
        ], 
        string="Sentido da Operação",
        default='outbound',
        required=True
    )
    
    centro = fields.Char(string='Centro')
    remessa = fields.Char(string='Remessa')
    
    canal_vendas = fields.Selection(
        [
            ('y001', 'Y001 (Distribuidor)'), 
            ('y002', 'Y002 (Key Account)'), 
            ('y004', 'Y004 (Venda Direta)'),
            ('y006', 'Y006 (Ex: Y006, CC0313)'),
            ('y055', 'Y055 (Exportação)'), 
            ('baldeio', 'Baldeio'),
            ('outros_canal', 'Outros')
        ], 
        string='Canal de Vendas'
    )
    
    prioridade_id = fields.Many2one(
        'lusitana_logistics.priority', 
        string='Prioridade'
    )
    
    # --- MUDANÇA (REQ 2): Lógica do Cliente ---
    cliente_code = fields.Char(string='Cód. Cliente (Referência)', 
                             help="Digite a Referência Interna (Código SAP) do cliente.")
    
    cliente_name = fields.Char(
        string='Nome Cliente', 
        compute='_compute_cliente_name', # Agora é um compute
        store=True, # Salva no banco de dados
        readonly=True
    )
    # --- FIM DA MUDANÇA ---                       
    placa_carreta = fields.Char(string='Placa Carreta')
    placa_cavalo = fields.Char(string='Placa Cavalo')
    deposito = fields.Char(string='Depósito')
    
    data_agendamento = fields.Date(string='Data Agendamento')
    hora_agendamento = fields.Char(string='Hora Agendamento')
    
    line_ids = fields.One2many('lusitana_logistics.agenda_heineken_line', 'agenda_id', string='Itens da Agenda')

    _sql_constraints = [
        ('dt_documento_uniq', 'unique (dt_documento)', 'Um registro com este DT já existe.')
    ]

    # --- NOVO MÉTODO COMPUTE (REQ 2) ---
    @api.depends('cliente_code')
    def _compute_cliente_name(self):
        for rec in self:
            if rec.cliente_code:
                partner = self.env['res.partner'].search(
                    [('ref', '=', rec.cliente_code)], limit=1
                )
                if partner:
                    rec.cliente_name = partner.name
                else:
                    rec.cliente_name = "!! CÓDIGO NÃO ENCONTRADO !!"
            else:
                rec.cliente_name = False

class AgendaHeinekenLine(models.Model):
    _name = 'lusitana_logistics.agenda_heineken_line'
    _description = 'Linha de Produto da Agenda de Carregamento'

    agenda_id = fields.Many2one('lusitana_logistics.agenda_heineken', string='Agenda', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Produto')
    
    product_descr_sap = fields.Char(string='Descrição (SAP)') # Coluna 'Descr. Material'
    
    quantidade = fields.Float(string='Quantidade') # Coluna 'Quantidade'
    quantidade_paletes = fields.Float(string='Qtd. Paletes') # Coluna 'PLT'