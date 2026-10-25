from odoo import models, fields

class LogisticaSaldoInsumo(models.Model):
    _name = 'logistica.saldo.rua.insumo'
    _description = 'Saldo de Estoque - INSUMOS'
    _rec_name = 'rua_endereco'
    _order = 'galpao, rua_endereco'

    galpao = fields.Char(string='Galpão', index=True)
    rua_endereco = fields.Char(string='Endereço (Rua)', required=True, index=True)
    
    produto_codigo = fields.Char(string='Código Insumo', index=True)
    produto_descricao = fields.Char(string='Descrição')
    
    qtd_pallets = fields.Float(string='Qtd Pallets/Embalagens', group_operator='sum')
    
    data_atualizacao = fields.Datetime(string='Última Sincronização', default=fields.Datetime.now)