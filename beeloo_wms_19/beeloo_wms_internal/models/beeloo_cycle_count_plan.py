# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BeelooCycleCountPlan(models.Model):
    _name = 'beeloo.cycle.count.plan'
    _description = 'Plano de Contagem Cíclica (Inventário)'# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BeelooCycleCountPlan(models.Model):
    _name = 'beeloo.cycle.count.plan'
    _description = 'Plano de Contagem Cíclica (Inventário)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nome do Plano', required=True, 
                       default=lambda self: f"Plano de Contagem {fields.Date.today().strftime('%d/%m/%Y')}")

    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('generated', 'Linhas Geradas'),
        ('in_progress', 'Contagem em Andamento'),
        ('done', 'Validado'),
        ('cancel', 'Cancelado')
    ], string='Status', default='draft', tracking=True)

    filter_location_ids = fields.Many2many('stock.location', string='Contar Localizações Específicas', domain="[('usage', '=', 'internal')]")
    filter_product_ids = fields.Many2many('product.product', string='Contar Produtos Específicos')
    filter_category_ids = fields.Many2many('product.category', string='Contar Categorias Específicas')

    line_ids = fields.One2many('beeloo.cycle.count.plan.line', 'plan_id', string='Linhas a Contar')
    
    # --- COMENTADO: O modelo stock.inventory.adjustment não existe no Odoo 19 ---
    # inventory_adjustment_id = fields.Many2one('stock.inventory.adjustment', string='Ajuste de Inventário', readonly=True, copy=False)

    def action_generate_lines(self):
        self.ensure_one()
        self.line_ids.unlink()
        domain = [('location_id.usage', '=', 'internal'), ('quantity', '>', 0)]
        if self.filter_location_ids: domain.append(('location_id', 'child_of', self.filter_location_ids.ids))
        if self.filter_product_ids: domain.append(('product_id', 'in', self.filter_product_ids.ids))
        if self.filter_category_ids: domain.append(('product_id.categ_id', 'child_of', self.filter_category_ids.ids)) 
        if len(domain) == 2: raise UserError(_("Selecione ao menos um filtro."))
        quants = self.env['stock.quant'].search(domain)
        plan_line_model = self.env['beeloo.cycle.count.plan.line']
        for quant in quants:
            plan_line_model.create({
                'plan_id': self.id,
                'product_id': quant.product_id.id,
                'location_id': quant.location_id.id,
                'lot_id': quant.lot_id.id,
                'theoretical_qty': quant.quantity,
            })
        self.write({'state': 'generated'})

    # --- MÉTODOS AJUSTADOS PARA COMPATIBILIDADE ---
    def action_start_count(self):
        self.ensure_one()
        if not self.line_ids: raise UserError(_("Gere as linhas primeiro."))
        
        # COMENTADO: Removendo criação de modelo inexistente no Odoo 19
        # adjustment = self.env['stock.inventory.adjustment'].create({
        #     'name': f"Contagem: {self.name}",
        #     'product_ids': [(6, 0, self.line_ids.product_id.ids)],
        #     'location_ids': [(6, 0, self.line_ids.location_id.ids)],
        # })
        # adjustment.action_start_inventory() 
        
        # AJUSTE: Apenas altera o estado para não quebrar a lógica do WMS
        # self.write({'inventory_adjustment_id': adjustment.id, 'state': 'in_progress'})
        self.write({'state': 'in_progress'})
        
        # return self.action_view_adjustment()
        return True
        
    def action_view_adjustment(self):
        self.ensure_one()
        # COMENTADO: Ação para modelo inexistente desativada
        # return {
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'stock.inventory.adjustment',
        #     'res_id': self.inventory_adjustment_id.id,
        #     'view_mode': 'form',
        #     'target': 'current',
        # }
        return True
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nome do Plano', required=True, 
                       default=lambda self: f"Plano de Contagem {fields.Date.today().strftime('%d/%m/%Y')}")

    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('generated', 'Linhas Geradas'),
        ('in_progress', 'Contagem em Andamento'),
        ('done', 'Validado'),
        ('cancel', 'Cancelado')
    ], string='Status', default='draft', tracking=True)

    filter_location_ids = fields.Many2many('stock.location', string='Contar Localizações Específicas', domain="[('usage', '=', 'internal')]")
    filter_product_ids = fields.Many2many('product.product', string='Contar Produtos Específicos')
    filter_category_ids = fields.Many2many('product.category', string='Contar Categorias Específicas')

    line_ids = fields.One2many('beeloo.cycle.count.plan.line', 'plan_id', string='Linhas a Contar')
    
    # --- CAMPO RESTAURADO ---
    #inventory_adjustment_id = fields.Many2one('stock.inventory.adjustment', string='Ajuste de Inventário', readonly=True, copy=False)

    def action_generate_lines(self):
        self.ensure_one()
        self.line_ids.unlink()
        domain = [('location_id.usage', '=', 'internal'), ('quantity', '>', 0)]
        if self.filter_location_ids: domain.append(('location_id', 'child_of', self.filter_location_ids.ids))
        if self.filter_product_ids: domain.append(('product_id', 'in', self.filter_product_ids.ids))
        if self.filter_category_ids: domain.append(('product_id.categ_id', 'child_of', self.filter_category_ids.ids)) 
        if len(domain) == 2: raise UserError(_("Selecione ao menos um filtro."))
        quants = self.env['stock.quant'].search(domain)
        plan_line_model = self.env['beeloo.cycle.count.plan.line']
        for quant in quants:
            plan_line_model.create({
                'plan_id': self.id,
                'product_id': quant.product_id.id,
                'location_id': quant.location_id.id,
                'lot_id': quant.lot_id.id,
                'theoretical_qty': quant.quantity,
            })
        self.write({'state': 'generated'})

    # --- MÉTODOS RESTAURADOS ---
    def action_start_count(self):
        self.ensure_one()
        if not self.line_ids: raise UserError(_("Gere as linhas primeiro."))
        
        adjustment = self.env['stock.inventory.adjustment'].create({
            'name': f"Contagem: {self.name}",
            'product_ids': [(6, 0, self.line_ids.product_id.ids)],
            'location_ids': [(6, 0, self.line_ids.location_id.ids)],
        })
        adjustment.action_start_inventory() # Inicia no Odoo
        
        # Vincula
        self.write({'inventory_adjustment_id': adjustment.id, 'state': 'in_progress'})
        
        return self.action_view_adjustment()
        
    def action_view_adjustment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.inventory.adjustment',
            'res_id': self.inventory_adjustment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
