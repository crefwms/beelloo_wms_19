from odoo import models, fields
class StockPicking(models.Model):
    _inherit = 'stock.picking'
    x_rma_id = fields.Char(string='RMA', tracking=True)
    x_motivo_devolucao = fields.Selection([
        ('arrependimento', 'Arrependimento (7 dias)'),
        ('defeito', 'Defeito Técnico'),
        ('errado', 'Produto Errado Enviado'),
        ('avaria', 'Avaria no Transporte'),
        ('nao_gostou', 'Não Gostou / Não Atendeu'),
    ], string='Motivo da Devolução', tracking=True)
    x_grading = fields.Selection([
        ('A', 'A-Grade (Novo)'),
        ('B', 'B-Grade (Outlet)'),
        ('C', 'C-Grade (Descarte)'),
        ('FRAUDE', 'Fraude Detectada'),
    ], string='Grading', tracking=True)
    x_motivo_grading = fields.Text(string='Observações do Grading')
    x_peso_coleta = fields.Float(string='Peso Coleta (g)', digits=(10, 2))
    x_peso_recebido = fields.Float(string='Peso Recebido (g)', digits=(10, 2))
