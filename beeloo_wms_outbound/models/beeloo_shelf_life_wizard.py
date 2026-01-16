# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class ShelfLifeQueryWizard(models.TransientModel):
    _name = 'beeloo.shelf.life.query.wizard' 
    _description = 'Assistente de Consulta de Shelf Life (Tabelão)'
    _inherit = ['beeloo.shelf.life.mixin']

    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    product_id = fields.Many2one('product.product', string='Produto (Opcional)')
    dt_number = fields.Char(string="Número da DT")
    partner_ref = fields.Char(related='partner_id.ref', string="Matrícula SAP", readonly=True)
    
    x_policy_type = fields.Selection(
        related='partner_id.x_policy_type',
        string="Política de Shelf Life",
        readonly=True
    )
    
    x_fixed_days_value = fields.Integer(
        related='partner_id.x_fixed_days_value',
        string="Dias Restantes Mínimos",
        readonly=True
    )
    
    x_shelf_life_percent = fields.Float(
        related='partner_id.x_shelf_life_percent',
        string="% Máximo de Vida Consumida",
        readonly=True
    )
    
    result_line_ids = fields.One2many(
        'beeloo.shelf.life.query.wizard.line', 
        'wizard_id', # <--- ...procura por este nome 'wizard_id'
        string='Estoque Encontrado'
    )

    def action_search_shelf_life(self):
        """
        A LÓGICA PRINCIPAL - AGORA LENDO 'stock.quant'
        """
        self.ensure_one()
        self.result_line_ids.unlink()
        
        # O Domínio de busca agora é em STOCK.QUANT
        domain = [
            ('quantity', '>', 0), 
            ('location_id.usage', '=', 'internal'), # Apenas estoque interno
            ('lot_id', '!=', False),                # Apenas estoque rastreado
            ('lot_id.create_date', '!=', False)     # Apenas lotes com data de produção/recebimento
        ]
        if self.product_id:
            domain.append(('product_id', '=', self.product_id.id))
            
        # 1. BUSCA O ESTOQUE REAL (stock.quant)
        all_quants = self.env['stock.quant'].search(domain)
        
        today = date.today()
        lines_to_create = []
        
        for quant in all_quants:
            # 2. CHAMA NOSSO MIXIN (a regra de negócio)
            max_age_days = self._get_max_age_days(quant.product_id, self.partner_id)
            
            status = 'reprovado'
            shelf_life_percentage = 0
            
            # Precisamos da Data de Produção/Recebimento do Lote
            # Em Pilares 2 e 3, definimos 'stock.lot.create_date' como essa data
            production_date = quant.lot_id.create_date.date()
            total_shelf_life = quant.product_id.product_tmpl_id.x_shelf_days
            
            if total_shelf_life > 0:
                lot_age_days = (today - production_date).days
                remaining_days = total_shelf_life - lot_age_days
                if remaining_days > 0:
                    shelf_life_percentage = (remaining_days / total_shelf_life) * 100
                
                # 3. A VERIFICAÇÃO (FEFO + Política)
                if max_age_days is None: # Sem regra, aprovado
                    status = 'aprovado'
                elif lot_age_days <= max_age_days:
                    status = 'aprovado'

            # Verifica se já existe um 'Flow' (exceção)
            existing_flow = self.env['beeloo.shelf.life.flow'].search([
                ('quant_id', '=', quant.id), # << MUDANÇA
                ('status', 'in', ['draft', 'sent', 'approved'])
            ], limit=1)
            
            lines_to_create.append({
                'quant_id': quant.id, # << MUDANÇA
                'status': status,
                'wizard_id': self.id,
                'flow_id': existing_flow.id,
                'shelf_life_percentage': shelf_life_percentage,
            })
            
        self.env['beeloo.shelf.life.query.wizard.line'].create(lines_to_create)
        
        # (O 'return' para reabrir o wizard é portado 1-para-1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resultado da Consulta de Shelf Life',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

# --- Linha do Wizard (Refatorada) ---
class ShelfLifeQueryWizardLine(models.TransientModel):
    _name = 'beeloo.shelf.life.query.wizard.line'
    _description = 'Linha de Resultado do Assistente de Shelf Life'

    wizard_id = fields.Many2one('beeloo.shelf.life.query.wizard', string="Wizard")
    
    # --- A GRANDE MUDANÇA ---
    quant_id = fields.Many2one('stock.quant', string="Posição de Estoque (Quant)", readonly=True)
    
    # Campos 'computed' que leem do 'quant_id'
    location_id = fields.Many2one(related='quant_id.location_id', readonly=True)
    product_id = fields.Many2one(related='quant_id.product_id', readonly=True)
    lot_id = fields.Many2one(related='quant_id.lot_id', readonly=True)
    total_quantity = fields.Float(related='quant_id.quantity', string='Total (Unidades)', readonly=True)
    production_date = fields.Datetime(
        related='lot_id.create_date', 
        string="Data de Produção"
    )
    
    status = fields.Selection([('aprovado', 'Aprovado'), ('reprovado', 'Reprovado')], string='Status')
    flow_id = fields.Many2one('beeloo.shelf.life.flow', string="Flow")
    flow_status = fields.Selection(related='flow_id.status', string="Status do Flow")
    shelf_life_percentage = fields.Float(string='Vida Útil Restante (%)')

    # (Ações 'action_print_line_report' e 'action_open_flow' são portadas,
    #  mas 'action_open_flow' precisa passar o 'quant_id' em vez do 'snapshot_line_id')
    
    def action_open_flow(self):
        self.ensure_one()
        flow = self.env['beeloo.shelf.life.flow'].create({
            'partner_id': self.wizard_id.partner_id.id,
            'product_id': self.product_id.id,
            'quant_id': self.quant_id.id, # << MUDANÇA
            'offered_date': self.production_date,
        })
        # (O 'return' para abrir o flow é portado 1-para-1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Abrir Flow',
            'res_model': 'beeloo.shelf.life.flow',
            'res_id': flow.id,
            'view_mode': 'form',
            'target': 'new',
        }