from odoo import models, fields, api

class OeaRisk(models.Model):
    _name = 'oea.risk'
    _description = 'SGSI - Gestão de Riscos'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Identificação do Risco', required=True)
    asset_id = fields.Many2one('oea.it.asset', string='Ativo Relacionado', required=True)
    
    threat = fields.Text(string='Ameaça', help='Ex: Incêndio, Invasão, Falha de Hardware')
    vulnerability = fields.Text(string='Vulnerabilidade', help='Ex: Ausência de extintores, Senhas fracas')
    
    impact = fields.Selection([
        ('1', 'Muito Baixo'),
        ('2', 'Baixo'),
        ('3', 'Médio'),
        ('4', 'Alto'),
        ('5', 'Muito Alto'),
    ], string='Impacto', default='3')
    
    probability = fields.Selection([
        ('1', 'Rara'),
        ('2', 'Pouco Provável'),
        ('3', 'Provável'),
        ('4', 'Muito Provável'),
        ('5', 'Quase Certa'),
    ], string='Probabilidade', default='3')
    
    risk_level = fields.Integer(string='Nível de Risco', compute='_compute_risk_level', store=True)
    risk_rating = fields.Selection([
        ('low', 'Baixo'),
        ('medium', 'Médio'),
        ('high', 'Alto'),
        ('critical', 'Crítico'),
    ], string='Classificação', compute='_compute_risk_level', store=True)

    treatment_strategy = fields.Selection([
        ('mitigate', 'Mitigar'),
        ('transfer', 'Transferir'),
        ('avoid', 'Evitar'),
        ('accept', 'Aceitar'),
    ], string='Estratégia de Tratamento')
    
    control_action = fields.Text(string='Ações de Controle / Mitigação')
    
    state = fields.Selection([
        ('draft', 'Identificado'),
        ('analysis', 'Em Análise'),
        ('treatment', 'Em Tratamento'),
        ('closed', 'Encerrado'),
    ], string='Status', default='draft', tracking=True)

    def action_analyze(self):
        self.write({'state': 'analysis'})

    def action_treat(self):
        self.write({'state': 'treatment'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company)

    @api.depends('impact', 'probability')
    def _compute_risk_level(self):
        for risk in self:
            impact = int(risk.impact or 0)
            prob = int(risk.probability or 0)
            level = impact * prob
            risk.risk_level = level
            
            if level <= 5: risk.risk_rating = 'low'
            elif level <= 12: risk.risk_rating = 'medium'
            elif level <= 19: risk.risk_rating = 'high'
            else: risk.risk_rating = 'critical'
