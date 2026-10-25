from odoo import models, fields, api  # <--- Faltava essa linha!

class VeiculoRastreabilidade(models.Model):
    _name = 'rastreabilidade.veiculo'
    _description = 'Cadastro de Veículos'
    _rec_name = 'placa'

    placa = fields.Char(string='Placa', required=True)
    tipo = fields.Selection([
        ('cavalo', 'Cavalo Mecânico'),
        ('carreta', 'Carreta'),
        ('implemento', 'Implemento')
    ], string='Tipo')
    transportadora_id = fields.Many2one('res.partner', string='Transportadora', domain=[('category_id.name', 'ilike', 'Transportadora')])