from odoo import models, fields, api

class LogisticaMovimento(models.Model):
    _name = 'logistica.movimento'
    _description = 'Movimentação Logística (Access)'
    _order = 'data_movimento desc, id desc'

    # Agora o Name será a NFe ou DT (Documento visual)
    name = fields.Char(string='Documento/Ref', required=True, index=True) 
    
    # Campo NOVO para guardar o ID do Access (logistica_xml_carga)
    registro_origem = fields.Integer(string='Reg. Origem (ID)', index=True, help="ID da tabela logistica_xml_carga")
    
    # Campo NOVO para NFe explícita
    nfe_numero = fields.Char(string='NFe', index=True)

    tipo = fields.Selection([
        ('entrada', 'Entrada'),
        ('saida', 'Saída')
    ], string='Tipo', required=True, index=True)
    
    produto_codigo = fields.Char(string='Cód. Produto', index=True)
    produto_descricao = fields.Char(string='Descrição do Produto')
    
    data_movimento = fields.Date(string='Data do Movimento', index=True)
    mes_ano = fields.Char(string='Mês/Ano')
    
    quantidade_pallets = fields.Integer(string='Qtd. Pallets')
    
    chave_unica = fields.Char(string='ID Único Externo', copy=False, index=True)

    _sql_constraints = [
        ('chave_unica_uniq', 'unique (chave_unica)', 'Este registro já foi importado! A chave única deve ser exclusiva.')
    ]