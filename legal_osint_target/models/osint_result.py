# -*- coding: utf-8 -*-
from odoo import models, fields

class OsintResult(models.Model):
    _name = 'osint.result'
    _description = 'Resultado de Monitoramento OSINT'
    _order = 'date desc'

    target_id = fields.Many2one('osint.target', string='Alvo', required=True, ondelete='cascade')
    name = fields.Char(string='Título do Resultado', required=True)
    date = fields.Datetime(string='Data do Resultado', default=fields.Datetime.now)
    process_number = fields.Char(string='Número do Processo')
    content = fields.Html(string='Conteúdo do Resultado')

    # Campo sugerido para o resumo mais detalhado
    summary = fields.Text(string='Resumo Curto')
