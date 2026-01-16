# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class BeelooDamageReport(models.Model):
    _name = 'beeloo.damage.report'
    _description = 'Boletim de Ocorrência de Avaria'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Referência', required=True, copy=False, readonly=True, 
                       default=lambda self: _('Novo'))

    state = fields.Selection([
        ('pending', 'Aguardando Decisão'),
        ('rework', 'Enviado para Retrabalho'),
        ('returned', 'Enviado para Devolução'),
        ('scrapped', 'Dado como Perda (Baixa)'),
        ('cancel', 'Cancelado')
    ], string='Status', default='pending', tracking=True)

    # --- Links ---
    picking_id = fields.Many2one('stock.picking', string="Recebimento", readonly=True)
    presentation_id = fields.Many2one('beeloo.presentation', string="Apresentação", readonly=True)
    move_line_id = fields.Many2one('stock.move.line', string="Linha de Recebimento Original", readonly=True)
    
    # Campo para linkar a nova linha de avaria que criamos
    x_damage_move_line_id = fields.One2many(
        'stock.move.line', 
        'x_damage_report_id', # Novo campo (ver Passo 4)
        string="Linha de Estoque Avariado"
    )

    # --- Detalhes ---
    product_id = fields.Many2one('product.product', string='Produto Avariado', readonly=True)
    lot_id = fields.Many2one('stock.lot', string='Lote/No. de Série', readonly=True)
    quantity_damaged = fields.Float(string="Quantidade Avariada", readonly=True)
    reason = fields.Text(string="Motivo da Avaria", readonly=True)
    
    # --- Decisão ---
    rework_order_id = fields.Many2one(
        'beeloo.rework', 
        string="Ordem de Retrabalho", 
        readonly=True, 
        copy=False
    )
    return_picking_id = fields.Many2one(
        'stock.picking', 
        string="Devolução (Saída)", 
        readonly=True, 
        copy=False
    )
    
    # 1. Responsável pelo Boletim (Quem preencheu)
    # Puxamos automaticamente o usuário que está logado
    responsible_user_id = fields.Many2one(
        'res.users', 
        string='Responsável (Beeloo)',
        default=lambda self: self.env.user,
        readonly=True,
        copy=False
    )
    
    # 2. Responsável pela Operação (Ex: O Conferente)
    # Pode ser o mesmo usuário ou o supervisor dele
    operation_user_id = fields.Many2one(
        'res.users', 
        string='Conferente (Operação)',
        default=lambda self: self.env.user,
        copy=False
    )
    
    # 3. Assinatura do Motorista
    driver_name_signed = fields.Char(
        string="Nome do Motorista (p/ Assinatura)",
        help="O motorista deve preencher o nome por extenso."
    )
    
    driver_document = fields.Char(
        string="Documento do Motorista (RG/CPF/CNH)"
    )
    
    driver_signature = fields.Image(
        string="Assinatura do Motorista",
        help="Use um pad de assinatura digital ou tire foto da assinatura no papel."
        # No Odoo 18, podemos usar um widget de assinatura!
        # widget="signature" 
    )
    
    @api.model_create_multi
    def create(self, vals_list):
        # (Lógica da Sequência 'beeloo.damage.report')
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('beeloo.damage.report') or _('Novo')
        return super().create(vals_list)

    # --- BOTÕES DE DECISÃO DO GERENTE ---
    def action_send_to_rework(self):
        """
        Cria a Ordem de Retrabalho (o 'mrp.unbuild' que definimos antes)
        """
        self.ensure_one()
        # 1. Cria a Ordem de Retrabalho (Pilar 3)
        rework_order = self.env['beeloo.rework'].create({
            'product_id': self.product_id.id,
            'product_qty': self.quantity_damaged,
            'lot_id': self.lot_id.id,
            'location_id': self.x_damage_move_line_id.location_dest_id.id, # Sai de 'Estoque/Avarias'
            'reason': self.reason,
            'origin': self.name,
        })
        
        # 2. Processa o retrabalho (a função que já criamos)
        rework_order.action_confirm_rework() 
        
        self.write({
            'rework_order_id': rework_order.id,
            'state': 'rework'
        })
        return True # (ou pode abrir a tela do rework_order)

    def action_send_to_return(self):
        """
        Cria um 'stock.picking' de SAÍDA para retornar à fábrica
        """
        self.ensure_one()
        # 1. Encontrar o Tipo de Operação de Devolução (Saída)
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'), # Devolução é uma SAÍDA
            # (Aqui podemos ter um 'x_is_return_type' para HNK)
        ], limit=1)

        # 2. Cria o Picking de Saída
        return_picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': self.x_damage_move_line_id.location_dest_id.id, # Sai de 'Estoque/Avarias'
            'location_dest_id': picking_type.default_location_dest_id.id, # Vai para 'Localização/Cliente'
            'origin': self.name,
        })
        
        # 3. Cria a linha de movimento
        self.env['stock.move'].create({
            'picking_id': return_picking.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity_damaged,
            'product_uom': self.product_id.uom_id.id,
            'location_id': return_picking.location_id.id,
            'location_dest_id': return_picking.location_dest_id.id,
            'name': self.product_id.name,
        })
        
        return_picking.action_confirm()
        return_picking.action_assign() # Reserva o estoque em 'Avarias'
        
        self.write({
            'return_picking_id': return_picking.id,
            'state': 'returned'
        })
        
        # 4. Abre a tela da Devolução
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': return_picking.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_print_bo(self):
        """
        Esta função é chamada pelo botão "Imprimir BO"
        Ela vai procurar um Relatório QWeb (PDF) chamado 'beeloo_wms_internal.report_damage'
        """
        self.ensure_one()
        # Vamos precisar criar este relatório (report_damage_template)
        return self.env.ref('beeloo_wms_internal.report_damage').report_action(self)    