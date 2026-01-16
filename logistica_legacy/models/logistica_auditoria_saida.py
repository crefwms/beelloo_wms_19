from odoo import models, fields, api

class LogisticaAuditoriaSaida(models.Model):
    _name = 'logistica.auditoria.saida'
    _description = 'Auditoria de Expedição (DT)'
    _rec_name = 'dt_numero'
    _order = 'data_dt desc'

    dt_numero = fields.Char(string='DT Número', required=True, index=True)
    data_dt = fields.Date(string='Data DT')

    
    # Dados Logísticos
    motorista = fields.Char(string='Motorista')
    placa = fields.Char(string='Placa')
    
    # Totais para visão rápida
    total_pallets_pedido = fields.Integer(string='Qtd. Pedida', compute='_compute_totais', store=True)
    total_pallets_separado = fields.Integer(string='Qtd. Separada', compute='_compute_totais', store=True)
    total_pallets_carregado = fields.Integer(string='Qtd. Carregada', compute='_compute_totais', store=True)
    
    # Status Geral da DT
    status_audit = fields.Selection([
        ('ok', '🟢 Tudo Certo'),
        ('warn', '🟡 Divergência Parcial'),
        ('erro', '🔴 Erro Crítico')
    ], string='Status Auditoria', compute='_compute_totais', store=True)

    linha_ids = fields.One2many('logistica.auditoria.saida.linha', 'auditoria_id', string="Produtos")

    @api.depends('linha_ids.status_linha', 'linha_ids.qtd_pedido', 'linha_ids.qtd_carregado')
    def _compute_totais(self):
        for rec in self:
            rec.total_pallets_pedido = sum(rec.linha_ids.mapped('qtd_pedido'))
            rec.total_pallets_separado = sum(rec.linha_ids.mapped('qtd_separada'))
            rec.total_pallets_carregado = sum(rec.linha_ids.mapped('qtd_carregado'))
            
            # Se qualquer linha tiver erro, a DT inteira fica vermelha
            if any(l.status_linha == 'erro' for l in rec.linha_ids):
                rec.status_audit = 'erro'
            elif any(l.status_linha == 'warn' for l in rec.linha_ids):
                rec.status_audit = 'warn'
            else:
                rec.status_audit = 'ok'

class LogisticaAuditoriaSaidaLinha(models.Model):
    _name = 'logistica.auditoria.saida.linha'
    _description = 'Linhas da Auditoria de Saída'

    auditoria_id = fields.Many2one('logistica.auditoria.saida', string="Auditoria Pai", ondelete='cascade')
    
    produto_codigo = fields.Char(string="Produto")
    qtd_pedido = fields.Integer(string="Pedido")
    qtd_separada = fields.Integer(string="Separação")
    qtd_carregado = fields.Integer(string="Carregado")
    
    # === ESTES SÃO OS CAMPOS QUE ESTÃO FALTANDO ===
    status_msg = fields.Char(string="Mensagem", compute='_compute_status', store=True)
    status_linha = fields.Selection([
        ('ok', 'OK'), 
        ('erro', 'Divergência')
    ], string="Status", compute='_compute_status', store=True)
    # ==============================================

    @api.depends('qtd_pedido', 'qtd_separada', 'qtd_carregado')
    def _compute_status(self):
        for rec in self:
            # Regra: Tudo tem que bater
            if rec.qtd_pedido == rec.qtd_separada == rec.qtd_carregado:
                rec.status_linha = 'ok'
                rec.status_msg = 'OK'
            
            # Regra: Carga diferente do Pedido
            elif rec.qtd_carregado != rec.qtd_pedido:
                rec.status_linha = 'erro'
                rec.status_msg = f'Div. Carga (Ped: {rec.qtd_pedido} vs Carg: {rec.qtd_carregado})'
            
            # Regra: Separação diferente do Pedido
            elif rec.qtd_separada != rec.qtd_pedido:
                rec.status_linha = 'erro'
                rec.status_msg = f'Div. Separação (Ped: {rec.qtd_pedido} vs Sep: {rec.qtd_separada})'
            
            # Qualquer outra coisa
            else:
                rec.status_linha = 'erro'
                rec.status_msg = 'Erro Geral'