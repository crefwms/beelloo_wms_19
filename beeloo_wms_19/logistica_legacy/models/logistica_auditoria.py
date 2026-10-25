from odoo import models, fields, api

class LogisticaAuditoria(models.Model):
    _name = 'logistica.auditoria'
    _description = 'Auditoria de Integridade (Access)'
    _rec_name = 'registro_origem'
    _order = 'registro_origem desc'

    registro_origem = fields.Integer(string='Registro (ID)', required=True, index=True)
    nfe_numero = fields.Char(string='NFe')
    produto_codigo = fields.Char(string='Cód. Produto')
    produto_descricao = fields.Char(string='Descrição')
    
    # O PILAR DA TRIANGULAÇÃO
    qtd_declarada = fields.Integer(string='Qtd. NFe (Header)', help="Qtd informada no cabeçalho da carga")
    qtd_gerada = fields.Integer(string='Qtd. Gerada (Loc)', help="Linhas criadas na tabela localização")
    qtd_saida = fields.Integer(string='Qtd. Saída', help="Soma das saídas na tabela saida_carga")
    
    # CÁLCULOS
    saldo_sistema = fields.Integer(string='Saldo Calculado', compute='_compute_saldos', store=True)
    divergencia_entrada = fields.Boolean(string='Erro Entrada?', compute='_compute_saldos', store=True)
    
    status = fields.Selection([
        ('ok', '🟢 Íntegro'),
        ('erro', '🔴 Divergência'),
        ('zerado', '⚪ Zerado/Fechado')
    ], string='Status', compute='_compute_saldos', store=True)

    @api.depends('qtd_declarada', 'qtd_gerada', 'qtd_saida')
    def _compute_saldos(self):
        for rec in self:
            # 1. Verifica se Header bate com Linhas
            rec.divergencia_entrada = rec.qtd_declarada != rec.qtd_gerada
            
            # 2. Calcula Saldo
            rec.saldo_sistema = rec.qtd_gerada - rec.qtd_saida
            
            # 3. Define Status
            if rec.divergencia_entrada:
                rec.status = 'erro'
            elif rec.saldo_sistema == 0:
                rec.status = 'zerado'
            elif rec.saldo_sistema < 0: # Saiu mais do que entrou? Erro grave!
                rec.status = 'erro'
            else:
                rec.status = 'ok'