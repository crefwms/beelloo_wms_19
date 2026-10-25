# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BeelooAgenda(models.Model):
    _name = 'beeloo.agenda'
    _description = 'Agenda de Operações (SAP ZRTMFB012)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'dt_documento'

    dt_documento = fields.Char(string='DT (Doc. Transporte)', required=True, index=True)
    
    presentation_id = fields.Many2one(
        'beeloo.presentation', 
        string="Apresentação Vinculada",
        copy=False,
        ondelete='cascade'
    )
    
    transportadora_id = fields.Many2one(
        'res.partner', 
        string='Transportadora', 
        domain="[('category_id.name', 'ilike', 'Transportadora')]" 
    )
    direction = fields.Selection(
        [
            ('inbound', 'Entrada/Inbound'), 
            ('outbound', 'Saída/Outbound')
        ], 
        string="Sentido da Operação",
        default='outbound',
        required=True
    )
    
    centro = fields.Char(string='Centro')
    remessa = fields.Char(string='Remessa')
    canal_vendas = fields.Selection(
        [
            ('y001', 'Y001 (Distribuidor)'), 
            ('y002', 'Y002 (Key Account)'), 
            ('y004', 'Y004 (Venda Direta)'),
            ('y006', 'Y006 (Ex: Y006, CC0313)'),
            ('y055', 'Y055 (Exportação)'), 
            ('baldeio', 'Baldeio'),
            ('outros_canal', 'Outros')
        ], 
        string='Canal de Vendas'
    )
    prioridade_id = fields.Many2one('beeloo.priority', string='Prioridade')
    cliente_code = fields.Char(string='Cód. Cliente (Referência)')
    
    # --- A CORREÇÃO (Bug #3) ---
    # (Campo NÃO é mais compute, é um Char normal)
    cliente_name = fields.Char(
        string='Nome Cliente', 
        readonly=True
    )
    # ---------------------------
    
    placa_carreta = fields.Char(string='Placa Carreta')
    placa_cavalo = fields.Char(string='Placa Cavalo')
    deposito = fields.Char(string='Depósito')
    data_agendamento = fields.Date(string='Data Agendamento', required=True)
    hora_agendamento = fields.Char(string='Hora Agendamento (ex: 14:30)')
    line_ids = fields.One2many('beeloo.agenda.line', 'agenda_id', string='Itens da Agenda')
    
    state = fields.Selection([
        ('draft', 'Agendado'),
        ('in_progress', 'Em Operação'),
        ('done', 'Concluído'),
        ('cancel', 'Cancelado')
    ], string="Status", default='draft', readonly=True, copy=False, tracking=True)
    
    stock_picking_id = fields.Many2one(
        'stock.picking', 
        string="Movimentação de Estoque", 
        readonly=True, 
        copy=False
    )


    _sql_constraints = [
       ('dt_documento_uniq', 'unique (dt_documento)', 'Um registro com este DT já existe.')
    ]

    # --- A CORREÇÃO (Bug #3) ---
    # (Mudou de @api.depends para @api.onchange E tem a lógica real)
    @api.onchange('cliente_code')
    def _compute_cliente_name(self):
        for rec in self:
            if rec.cliente_code:
                # O campo 'ref' é o 'Referência Interna' padrão do Odoo
                partner = self.env['res.partner'].search(
                    [('ref', '=', rec.cliente_code)], limit=1
                )
                if partner:
                    rec.cliente_name = partner.name
                else:
                    rec.cliente_name = "!! CÓDIGO NÃO ENCONTRADO !!"
            else:
                rec.cliente_name = False

    # --- A "PONTE" v1.4 (A "Cirurgia Final") ---
    def action_create_picking(self):
        """
        BOTÃO (na linha da Agenda): Cria o Picking (Inbound ou Outbound).
        Esta é a NOVA "Ponte" (Pilar 1 -> Pilar 2).
        """
        self.ensure_one()
        presentation = self.presentation_id # O "Pai"
        
        if self.stock_picking_id:
            raise UserError(_("Esta DT (Agenda) já possui uma Movimentação de Estoque (%s).") % self.stock_picking_id.name)
        
        if presentation.state not in ('ready', 'in_progress'):
             raise UserError(_("A Apresentação (%s) ainda não está 'Pronta para Operação'. Verifique o status da Troca de NF.") % presentation.name)
        
        # 1. Encontrar o Tipo de Operação (Inbound ou Outbound)
        if self.direction == 'inbound':
            picking_type_code = 'incoming'
        elif self.direction == 'outbound':
            picking_type_code = 'outgoing'
        else:
            raise UserError(_("A Direção da DT não é válida (Inbound/Outbound)."))

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', picking_type_code),
            ('warehouse_id', '!=', False) # (Pega o 1º armazém)
        ], limit=1)
        
        if not picking_type:
            raise UserError(_("Não foi possível encontrar um Tipo de Operação '%s' para um armazém ativo.") % picking_type_code)

        # 2. Preparar os dados para o `stock.picking`
        picking_vals = {
            'origin': f"{presentation.name} / {self.dt_documento}",
            'partner_id': presentation.partner_id.id, # (Puxa do "Pai")
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'x_presentation_id': presentation.id, # O VÍNCULO!
            'state': 'draft',
        }
        
        # 3. Criar o Picking
        picking = self.env['stock.picking'].create(picking_vals)
        
        # --- A CORREÇÃO (v1.4 - O "Pulo do Gato") ---
        # 4. Anexar o XML da NFe HNK (do "Pai") ao "Neto" (o Picking)
        if self.direction == 'inbound' and presentation.requires_nf_exchange and presentation.hnk_nf_xml:
            self.env['ir.attachment'].create({
                'name': f"NFe_{presentation.hnk_nf_number or self.dt_documento}.xml",
                'datas': presentation.hnk_nf_xml,
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'description': 'XML da NFe HNK (Copiado da Apresentação)',
            })
            picking.message_post(body="XML da NFe HNK anexado automaticamente a partir da Apresentação.")
        # -----------------------------------------------

        # 5. Preencher as linhas do picking com as linhas da agenda
        for agenda_line in self.line_ids:
            if agenda_line.product_id: # Se o DE/PARA do SKU funcionou
                self.env['stock.move'].create({
                    'picking_id': picking.id,
                    'product_id': agenda_line.product_id.id,
                    'product_uom_qty': agenda_line.quantidade,
                    'product_uom': agenda_line.product_id.uom_id.id,
                    'name': agenda_line.product_descr_sap or agenda_line.product_id.name,
                })

        # 6. Salva o link no "Filho" e muda o status
        self.write({
            'stock_picking_id': picking.id,
            'state': 'in_progress'
        })
        presentation.write({'state': 'in_progress'})
        
        # 7. Abre a tela do Picking para o operador
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'target': 'current',
        }
        

    @api.onchange('dt_documento')
    def _onchange_dt_documento_autofill(self):
        """
        Ao digitar a DT na linha, busca na Agenda (SAP)
        e preenche os campos automaticamente.
        """
        if not self.dt_documento:
            # Limpa os campos se a DT for apagada
            self.direction = False
            self.transportadora_id = False
            self.prioridade_id = False
            self.cliente_code = False
            self.cliente_name = False # (Não se esqueça deste)
            self.placa_carreta = False
            self.placa_cavalo = False
            self.data_agendamento = False
            self.hora_agendamento = False
            self.line_ids = [(5, 0, 0)]
            return

        existing_agenda = self.env['beeloo.agenda'].search([
            ('dt_documento', '=', self.dt_documento),
            ('presentation_id', '=', False),
            ('state', '=', 'draft')
        ], limit=1)
        
        if existing_agenda:
            # 2. Se achou, "rouba" os dados dela!
            self.direction = existing_agenda.direction
            self.transportadora_id = existing_agenda.transportadora_id
            self.prioridade_id = existing_agenda.prioridade_id
            self.cliente_code = existing_agenda.cliente_code
            self.placa_carreta = existing_agenda.placa_carreta
            self.placa_cavalo = existing_agenda.placa_cavalo
            self.data_agendamento = existing_agenda.data_agendamento
            self.hora_agendamento = existing_agenda.hora_agendamento

            # (Copia as linhas de "Itens")
            self.line_ids = [(5, 0, 0)] # Limpa
            self.line_ids = [
                (0, 0, {
                    'product_sku_sap': line.product_sku_sap,
                    'product_descr_sap': line.product_descr_sap,
                    'quantidade': line.quantidade,
                    'quantidade_paletes': line.quantidade_paletes,
                }) for line in existing_agenda.line_ids
            ]
            
            # (Chama o outro onchange para preencher o nome do cliente)
            self._compute_cliente_name() 
            
            return {
                'warning': {
                    'title': 'DT Encontrada na Agenda!',
                    'message': f'Os dados da DT {self.dt_documento} foram pré-carregados.'
                }
            }

# --- Classe BeelooAgendaLine (Sem alterações, está correta) ---
class BeelooAgendaLine(models.Model):
    _name = 'beeloo.agenda.line'
    _description = 'Linha de Produto da Agenda de Operações'

    agenda_id = fields.Many2one('beeloo.agenda', string='Agenda', ondelete='cascade', required=True)
    product_sku_sap = fields.Char(string='SKU (SAP)', help="Código do produto vindo do SAP.")
    product_id = fields.Many2one(
        'product.product', 
        string='Produto (Beeloo)',
        compute='_compute_product_id',
        store=True
    )
    product_descr_sap = fields.Char(string='Descrição (SAP)')
    quantidade = fields.Float(string='Quantidade (Unid. Medida)') 
    quantidade_paletes = fields.Float(string='Qtd. Paletes')

    @api.depends('product_sku_sap')
    def _compute_product_id(self):
        for line in self:
            if line.product_sku_sap:
                product = self.env['product.product'].search(
                    [('x_sku', '=', line.product_sku_sap)], limit=1
                )
                line.product_id = product.id or False
            else:
                line.product_id = False