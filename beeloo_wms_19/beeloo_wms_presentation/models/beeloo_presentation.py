# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class BeelooPresentation(models.Model):
    _name = 'beeloo.presentation'
    _description = 'Apresentação de Veículo (Portaria WMS)'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Apresentação', required=True, copy=False, readonly=True, 
        default=lambda self: _('Novo')
    )
    
    #--- Ponto 4: Vários Agendamentos (O2M v1.1) ---
    agenda_ids = fields.One2many(
        'beeloo.agenda', 
        'presentation_id',
        string="Agendas Vinculadas (DTs)"
    )
    
    # --- Ponto 2: Transportadora e Motorista ---
    partner_id = fields.Many2one(
        'res.partner', 
        string='Transportadora',
        domain="[('category_id.name', '=', 'Transportadora')]",
        required=True
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Motorista',
        domain="[('is_motorist', '=', True)]", 
        required=True
    )
    
    # --- Ponto 3: Veículos (Tração) ---
    vehicle_id = fields.Many2one(
        'beeloo.vehicle',
        string='Veículo (Tração)',
        domain="[('tipo_frota', 'in', ('tracao', 'completo'))]",
        required=True
    )
    
    implement_line_ids = fields.One2many(
        'beeloo.presentation.implement.line',
        'presentation_id',
        string="Implementos (Carretas)"
    )
    
    lacre_line_ids = fields.One2many(
        'beeloo.presentation.lacre.line',
        'presentation_id',
        string="Lacres"
    )

    presentation_time = fields.Datetime(
        string='Horário da Apresentação', 
        default=fields.Datetime.now,
        required=True
    )

    # --- Workflow (Com a Troca de NF) ---
    state = fields.Selection(
        selection=[
            ('draft', 'Chegada (Portaria)'),
            ('nf_exchange', 'Triagem / Doc'),
            ('ready', 'Aguardando Pátio'),
            ('docked', 'Em Doca'),
            ('in_progress', 'Operando (Carga/Descarga)'),
            ('op_done', 'Operação Finalizada'),
            ('exit_allowed', 'Liberado Saída'),
            ('done', 'Saiu (Gate Out)'),
            ('cancel', 'Cancelado'),
        ],
        string='Status', default='draft', required=True, tracking=True, index=True
    )
    
    
    
    # --- Apêndice de Troca de NF ---
    requires_nf_exchange = fields.Boolean(
        string='Requer Troca de NF?',
        help="Marque se este motorista veio com a NF do fornecedor e precisa da NF da HNK para entrar."
    )
    original_nf_number = fields.Char(string='NF Original (Fornecedor)')
    hnk_nf_xml = fields.Binary(string='XML NF HNK')
    hnk_nf_number = fields.Char(string='NF HNK (Armazenagem)')
    
    # --- Vínculo com Estoque ---
    stock_picking_ids = fields.One2many(
        'stock.picking', 'x_presentation_id', string='Movimentações de Estoque'
    )
    

    def action_set_docked(self):
        """ Encostou na Doca """
        self.write({'state': 'docked'})

    def action_set_exit_allowed(self):
        """ Conferência Final OK - Pode Sair """
        self.write({'state': 'exit_allowed'})

    def action_gate_out(self):
        """ O caminhão cruzou o portão para fora """
        self.write({
            'state': 'done',
            # Aqui poderíamos salvar data_saida = fields.Datetime.now()
        })

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        if self.driver_id and self.driver_id.x_is_blocked:
            # Se o motorista estiver bloqueado, avisa o usuário
            return {
                'warning': {
                    'title': 'Motorista Bloqueado!',
                    'message': f"O motorista {self.driver_id.name} está bloqueado.\nMotivo: {self.driver_id.x_block_reason}\nOrigem: {self.driver_id.x_block_source}"
                }
            }
        if self.driver_id and self.driver_id.validade_integracao and self.driver_id.validade_integracao < fields.Date.today():
            # Se a integração estiver vencida
            return {
                'warning': {
                    'title': 'Integração Vencida!',
                    'message': f"A integração do motorista {self.driver_id.name} venceu em {self.driver_id.validade_integracao}."
                }
            }
            
    def action_confirm_nf_exchange(self):
        """ Botão: Confirma que a troca de NF foi feita E CRIA O PICKING. """
        self.ensure_one()
        self.write({'state': 'ready'})
        return True # Retorno para o client

    def action_skip_nf_exchange(self):
        """ Botão: Pula a troca de NF. """
        self.ensure_one()
        # NÃO CRIA MAIS O PICKING! Apenas libera o caminhão.
        self.write({'state': 'ready'})
        return True
    
    # --- INTERCEPTOR (FUNÇÃO 1/3) ---
    @api.model
    def _link_existing_agendas(self, presentation_id, agenda_commands):
        """
        Esta função é o "Interceptor".
        Ela varre os comandos de "CRIAR" (0, ...) e os 
        transforma em "LINKAR" (4, ...) se a DT já existir.
        """
        new_commands = []
        agendas_to_link = self.env['beeloo.agenda']
        
        for command in agenda_commands:
            # (0, 'virtual_id', {vals}) -> COMANDO DE CRIAR
            if command[0] == 0: 
                vals = command[2]
                dt = vals.get('dt_documento')
                
                if dt:
                    # Tenta achar a DT no banco, desde que não esteja em outra Apresentação
                    existing_agenda = self.env['beeloo.agenda'].search([
                        ('dt_documento', '=', dt),
                        ('presentation_id', '=', False),
                        ('state', '=', 'draft')
                    ], limit=1)
                    
                    if existing_agenda:
                        # ACHAMOS! Vamos "transformar" o comando.
                        # 1. Adiciona o comando de LINKAR (4, id, False)
                        new_commands.append((4, existing_agenda.id, False))
                        
                        # 2. Salva a agenda para ser vinculada
                        agendas_to_link |= existing_agenda
                        
                        # 3. Pula o comando de "CRIAR" original
                        continue 
            
            # Se não for (0, ...) ou se a DT não foi encontrada,
            # mantém o comando original (seja ele um (1,...), (2,...) ou um (0,...) para DT nova)
            new_commands.append(command)
            
        # Agora, vincula o ID do "Pai" em todas as agendas que "linkamos"
        if agendas_to_link:
            # Usamos 'sudo()' para garantir a permissão de escrita, 
            # já que o onchange pode ter bagunçado as permissões
            agendas_to_link.sudo().write({'presentation_id': presentation_id})
            
        return new_commands

    # --- INTERCEPTOR (FUNÇÃO 2/3) ---
    def write(self, vals):
        """ Sobrescreve o 'write' para interceptar o 'save' (em um registro existente). """
        if 'agenda_ids' in vals:
            # Roda o "Interceptor"
            vals['agenda_ids'] = self._link_existing_agendas(self.id, vals['agenda_ids'])
            
        return super(BeelooPresentation, self).write(vals)

    # --- INTERCEPTOR (FUNÇÃO 3/3 - FUSÃO) ---
    @api.model_create_multi
    def create(self, vals_list):
        """ 
        Sobrescreve o 'create' (em um registro novo).
        Esta é a FUSÃO da sua lógica de sequência + minha lógica de "Interceptor".
        """
        
        # --- Lógica da Sequência (Sua lógica original) ---
        for vals in vals_list:
            if vals.get('name', _('Novo')) == _('Novo'):
                # Puxa a sequência que você criou no XML!
                vals['name'] = self.env['ir.sequence'].next_by_code('beeloo.presentation') or _('Novo')
        
        # --- Lógica do Interceptor (Minha lógica) ---
        # Primeiro, cria o(s) "Pai" para que tenhamos um ID
        presentations = super(BeelooPresentation, self).create(vals_list)
        
        # Agora, itera em cada "Pai" criado e processa seus "Filhos"
        for i, presentation in enumerate(presentations):
            vals = vals_list[i]
            if 'agenda_ids' in vals.get('agenda_ids', []): # Garante que a lista existe
                # Roda o "Interceptor"
                processed_commands = self._link_existing_agendas(presentation.id, vals['agenda_ids'])
                
                # O 'write' é necessário porque o 'create' já passou
                # Usamos sudo() por segurança, caso as permissões do 'create' não sejam suficientes
                presentation.sudo().write({'agenda_ids': processed_commands})
                
        return presentations

    # --- FERRAMENTA DE RESET (PARA TESTES) ---
    def action_hard_reset(self):
        """
        Botão de Pânico/Teste:
        1. Cancela e Apaga todos os Pickings vinculados.
        2. Limpa campos de vínculo.
        3. Volta status para Rascunho.
        Isso permite re-testar o mesmo DT sem erro de duplicidade.
        """
        for pres in self:
            # Busca pickings vinculados a esta apresentação
            pickings = self.env['stock.picking'].search([
                ('x_presentation_id', '=', pres.id)
            ])
            
            for p in pickings:
                if p.state != 'cancel':
                    p.action_cancel() # Cancela reserva
                
                # Tenta apagar. Se tiver amarração contábil, deixa cancelado.
                try:
                    p.unlink()
                except Exception:
                    pass 
            
            # Reseta campos e status
            pres.write({
                'state': 'draft', # ou o estado inicial do seu fluxo
                # 'hnk_nf_xml': False, # Opcional: limpar o XML se quiser
            })
            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }