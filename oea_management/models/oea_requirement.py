from odoo import models, fields

class OeaRequirement(models.Model):
    _name = 'oea.requirement'
    _description = 'OEA Requirement'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Requirement ID/Name', required=True, tracking=True)
    description = fields.Html(string='Description')
    orientation = fields.Html(string='Orientation', help='Guidance on how to comply')
    
    type = fields.Selection([
        ('operational', 'Operacional'),
        ('documentary', 'Documental'),
        ('systemic', 'Sistêmico'),
        ('managerial', 'Gerencial'),
    ], string='Type', tracking=True)
    
    modality = fields.Selection([
        ('compliance', 'OEA-Conformidade'),
        ('security', 'OEA-Segurança'),
        ('both', 'Ambas'),
    ], string='Modality', default='both', tracking=True)
    
    complexity = fields.Selection([
        ('low', '🟢 Baixa'),
        ('medium', '🟡 Média'),
        ('high', '🔴 Alta'),
    ], string='Complexity', tracking=True)
    
    active = fields.Boolean(default=True)
    
    reference = fields.Char(string='Legal Reference', help='Article/Inciso/Alínea - ex: IN RFB 1.985/2020')
    category = fields.Char(string='Category', help='Trello List name')
    trello_card_id = fields.Char(string='Trello Card ID', help='Internal mapping for sync')
