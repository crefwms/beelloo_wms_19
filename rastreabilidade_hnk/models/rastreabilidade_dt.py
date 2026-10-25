# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RastreabilidadeDT(models.Model):
    _name = 'rastreabilidade.dt'
    _description = 'Documento de Transporte'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'numero_dt'

    numero_dt = fields.Char(string='Número DT', required=True, tracking=True)
    nfe = fields.Char(string='NFe', tracking=True)
    registro = fields.Char(string='Registro', tracking=True)
    tipo = fields.Selection([
        ('baldeio', 'Baldeio'),
        ('transferencia', 'Transferência'),
        ('devolucao', 'Devolução')
    ], string='Tipo', required=True)
    data = fields.Date(string='Data', default=fields.Date.context_today, tracking=True)
    
    # Relacionamentos com os domínios que você solicitou
    motorista_id = fields.Many2one(
        'res.partner', 
        string='Motorista', 
        domain=[('category_id.name', 'ilike', 'Motorista')],
        tracking=True
    )
    placa_cavalo_id = fields.Many2one(
        'rastreabilidade.veiculo', 
        string='Placa Cavalo', 
        domain=[('tipo', '=', 'cavalo')]
    )
    placa_carreta_id = fields.Many2one(
        'rastreabilidade.veiculo', 
        string='Placa Carreta', 
        domain=[('tipo', '=', 'carreta')]
    )

    # Campos de Avaria e Evidência
    foto_avaria = fields.Binary(string='Foto da Avaria')
    informacao_extra = fields.Text(string='Observações')

    state = fields.Selection([
        ('rascunho', 'Rascunho'),
        ('conferencia', 'Em Conferência'),
        ('concluido', 'Concluído')
    ], default='rascunho', string="Status", tracking=True)

    produto_conferencia_id = fields.Many2one('product.product', string="Produto em Conferência")
    
    # Este é o campo que vai receber o BIP
    barcode_scan = fields.Char(string="Escanear Etiqueta")

    linha_ids = fields.One2many('rastreabilidade.dt.linha', 'dt_id', string='Linhas')

    def action_iniciar(self):
        self.state = 'conferencia'

    def action_concluir(self):
        self.state = 'concluido'

    # Lógica para criar a linha automaticamente ao bipar
    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        if self.barcode_scan and self.produto_conferencia_id:
            # Cria a nova linha com o produto selecionado no cabeçalho
            nova_linha = self.env['rastreabilidade.dt.linha'].new({
                'dt_id': self._origin.id,
                'barcode_lido': self.barcode_scan,
                'produto_id': self.produto_conferencia_id.id,
                'data_leitura': fields.Datetime.now(),
            })
            self.linha_ids += nova_linha
            # Limpa o campo de scan para o próximo bip
            self.barcode_scan = False
    

class RastreabilidadeDTLinha(models.Model):
    _name = 'rastreabilidade.dt.linha'
    _description = 'Linhas de Etiquetas Bipadas'

    dt_id = fields.Many2one('rastreabilidade.dt', string='DT Referência', ondelete='cascade')
    
    # Dados da Etiqueta
    barcode_lido = fields.Char(string='Código da Etiqueta', required=True)
    produto_id = fields.Many2one('product.product', string='Produto')
    
    # Metadados
    data_leitura = fields.Datetime(string='Hora do Bip', default=fields.Datetime.now, readonly=True)
    tem_avaria = fields.Boolean(string='Avaria?')

    # Validação para não bipar a mesma etiqueta no mesmo DT
    _sql_constraints = [
        ('barcode_uniq', 'unique(dt_id, barcode_lido)', 'Esta etiqueta já foi bipada neste documento!')
    ]