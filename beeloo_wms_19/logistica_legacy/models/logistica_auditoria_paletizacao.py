from odoo import models, fields, api

class LogisticaAuditoriaPaletizacao(models.Model):
    _name = 'logistica.auditoria.paletizacao'
    _description = 'Auditoria de Paletização (Pack vs Pallet)'
    _rec_name = 'registro_carga'
    _order = 'registro_carga desc'

    # MUDANÇA 1: De Char para Integer (Agora é número de verdade!)
    registro_carga = fields.Integer(string='ID Carga', required=True, index=True)
    
    # MUDANÇA 2: Campo Data
    data_registro = fields.Date(string='Data')

    produto_codigo = fields.Char(string='Produto', index=True)
    
    qtd_unidades = fields.Float(string='Qtd. Unidades (XML)')
    paletizacao_padrao = fields.Integer(string='Padrão')
    
    pallets_sistema = fields.Float(string='Pallets (Carga)')
    pallets_teorico = fields.Float(string='Pallets (Calc)', compute='_compute_calculo', store=True)
    
    # MUDANÇA 3: Contagem de Locações
    qtd_locacoes = fields.Integer(string='Locações Criadas') 

    diferenca = fields.Float(string='Diferença', compute='_compute_calculo', store=True)
    
    status = fields.Selection([
        ('ok', '🟢 Bateu'),
        ('erro', '🔴 Divergência'),
        ('warn', '🟡 Sem Cadastro')
    ], string='Status', compute='_compute_calculo', store=True)

    @api.depends('qtd_unidades', 'paletizacao_padrao', 'pallets_sistema')
    def _compute_calculo(self):
        for rec in self:
            if rec.paletizacao_padrao <= 0:
                rec.pallets_teorico = 0
                rec.diferenca = 0
                rec.status = 'warn'
                continue

            rec.pallets_teorico = rec.qtd_unidades / rec.paletizacao_padrao
            rec.diferenca = round(rec.pallets_teorico - rec.pallets_sistema, 2)
            
            if abs(rec.diferenca) <= 0.01:
                rec.status = 'ok'
            else:
                rec.status = 'erro'