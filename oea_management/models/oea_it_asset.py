from odoo import models, fields, api

class OeaItAsset(models.Model):
    _name = 'oea.it.asset'
    _description = 'SGSI - Ativo de Tecnologia da Informação'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, name'

    name = fields.Char(string='Nome do Ativo', required=True)
    
    asset_tag = fields.Char(string='Tag de Ativo')
    
    category = fields.Selection([
        ('hardware', 'Hardware'),
        ('software', 'Software'),
        ('network', 'Rede'),
        ('data', 'Dados/Informação'),
        ('service', 'Serviço'),
    ], string='Categoria', required=True, default='hardware')
    
    classification = fields.Selection([
        ('public', 'Público'),
        ('internal', 'Interno'),
        ('confidential', 'Confidencial'),
        ('restricted', 'Restrito'),
    ], string='Classificação', required=True, default='internal')
    
    criticality = fields.Selection([
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ], string='Criticidade', required=True, default='medium')
    
    description = fields.Html(string='Descrição')
    
    partner_id = fields.Many2one('res.partner', string='Fornecedor', ondelete='set null')
    
    vendor_id = fields.Many2one('res.partner', string='Fabricante/Vendor', ondelete='set null')
    
    serial_number = fields.Char(string='Número de Série')
    
    lot_number = fields.Char(string='Número de Lote')
    
    barcode = fields.Char(string='Código de Barras')
    
    product_id = fields.Many2one('product.product', string='Produto Relacionado', ondelete='set null')
    
    location_id = fields.Many2one('stock.location', string='Localização', ondelete='set null')
    
    assigned_to = fields.Many2one('hr.employee', string='Responsável/Usuário', ondelete='set null')
    
    department_id = fields.Many2one('hr.department', string='Departamento', ondelete='set null')
    
    purchase_date = fields.Date(string='Data de Aquisição')
    warranty_end_date = fields.Date(string='Fim da Garantia')
    
    cost = fields.Float(string='Custo')
    currency_id = fields.Many2one('res.currency', string='Moeda', ondelete='set null')
    
    odoo_model_id = fields.Many2one(
        'ir.model',
        string='Registro Odoo Vinculado',
        ondelete='set null'
    )
    odoo_record_id = fields.Integer(string='Registro Odoo ID')
    
    incident_count = fields.Integer(string='Incidentes', compute='_compute_incident_count')
    
    active = fields.Boolean(default=True)
    
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company
    )
    
    def _compute_incident_count(self):
        for asset in self:
            domain = [
                ('asset_id', '=', asset.id),
                ('state', '!=', 'done'),
            ]
            asset.incident_count = self.env['oea.security.incident'].search_count(domain)
    
    def action_view_incidents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Incidentes',
            'res_model': 'oea.security.incident',
            'view_mode': 'list,form',
            'domain': [('asset_id', '=', self.id)],
            'context': {},
        }
