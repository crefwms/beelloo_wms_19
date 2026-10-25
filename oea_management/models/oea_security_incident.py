from odoo import models, fields, api
from datetime import datetime, timedelta

class OeaSecurityIncident(models.Model):
    _name = 'oea.security.incident'
    _description = 'SGSI - Incidente de Segurança'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'incident_date desc, priority desc, id'

    name = fields.Char(string='Código', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: 'New')
    
    incident_date = fields.Datetime(string='Data do Incidente', required=True, default=fields.Datetime.now)
    
    detection_date = fields.Datetime(string='Data de Detecção', required=True, default=fields.Datetime.now)
    
    incident_type = fields.Selection([
        ('malware', 'Malware/Vírus'),
        ('phishing', 'Phishing'),
        ('unauthorized_access', 'Acesso Não Autorizado'),
        ('data_leak', 'Vazamento de Dados'),
        ('ddos', 'Ataque DDoS'),
        ('physical', 'Violação Física'),
        ('insider', 'Ameaça Interna'),
        ('other', 'Outro'),
    ], string='Tipo de Incidente', required=True)
    
    severity = fields.Selection([
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ], string='Severidade', required=True, default='medium')
    
    priority = fields.Selection([
        ('0', 'Baixa'),
        ('1', 'Média'),
        ('2', 'Alta'),
        ('3', 'Urgente'),
    ], string='Prioridade', default='1')
    
    state = fields.Selection([
        ('new', 'Novo'),
        ('investigating', 'Investigando'),
        ('contained', 'Contido'),
        ('resolved', 'Resolvido'),
        ('closed', 'Fechado'),
    ], string='Status', default='new', tracking=True)
    
    description = fields.Html(string='Descrição', required=True)
    
    root_cause = fields.Html(string='Causa Raiz')
    
    resolution = fields.Html(string='Resolução')
    
    asset_id = fields.Many2one('oea.it.asset', string='Ativo Afetado')
    
    user_id = fields.Many2one('res.users', string='Usuário Afetado')
    
    employee_id = fields.Many2one('hr.employee', string='Funcionário Envolvido')
    
    partner_id = fields.Many2one('res.partner', string='Parceiro/Fornecedor')
    
    category_id = fields.Many2one('oea.requirement', string='Requisito Relacionado')
    
    requirement_item_id = fields.Many2one('oea.requirement.item', string='Item de Ação')
    
    affect_operations = fields.Boolean(string='Afeta Operações')
    
    affect_compliance = fields.Boolean(string='Afeta Conformidade')
    
    notify_authorities = fields.Boolean(string='Notificar Autoridades')
    
    notify_authorities_date = fields.Datetime(string='Data de Notificação')
    
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment',
        'oea_incident_evidence_rel',
        'incident_id',
        'attachment_id',
        string='Evidências'
    )
    
    action_ids = fields.One2many('oea.security.incident.action', 'incident_id', string='Ações Tomadas')
    
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )
    
    active = fields.Boolean(default=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('oea.security.incident') or 'INC/' + fields.Datetime.now().strftime('%Y%m%d%H%M%S')
        return super().create(vals_list)
    
    def action_investigate(self):
        self.write({'state': 'investigating'})
    
    def action_contain(self):
        self.write({'state': 'contained'})
    
    def action_resolve(self):
        self.write({'state': 'resolved'})
    
    def action_close(self):
        self.write({'state': 'closed'})
    
    def action_reopen(self):
        self.write({'state': 'new'})


class OeaSecurityIncidentAction(models.Model):
    _name = 'oea.security.incident.action'
    _description = 'SGSI - Ação de Incidente'
    
    incident_id = fields.Many2one('oea.security.incident', string='Incidente', required=True, ondelete='cascade')
    
    action_date = fields.Datetime(string='Data', required=True, default=fields.Datetime.now)
    
    description = fields.Html(string='Descrição da Ação', required=True)
    
    performed_by = fields.Many2one('res.users', string='Responsável', required=True, default=lambda self: self.env.user)
    
    action_type = fields.Selection([
        ('containment', 'Contenção'),
        ('eradication', 'Erradicação'),
        ('recovery', 'Recuperação'),
        ('notification', 'Notificação'),
        ('evidence', 'Coleta de Evidência'),
    ], string='Tipo de Ação', required=True)
    
    result = fields.Selection([
        ('success', 'Sucesso'),
        ('partial', 'Parcial'),
        ('failed', 'Falhou'),
    ], string='Resultado')
