# -*- coding: utf-8 -*-
# models/vehicle_presentation.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import base64

class VehiclePresentation(models.Model):
    _name = 'lusitana_logistics.vehicle_presentation'
    _description = 'Registro de Apresentação de Veículo'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Nº Apresentação', required=True, copy=False, readonly=True, index=True, default='Novo') 

    state = fields.Selection([
        ('rascunho', 'Rascunho'),
        ('aguardando', 'Aguardando'),
        ('entrada', 'Entrada no Pátio'),
        ('em_operacao', 'Em Operação'),
        ('ato', 'Aguardando ATO'),
        ('monitoramento', 'Monitoramento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ], string='Status', default='rascunho', tracking=True)

    # --- CAMPOS DE RASTREABILIDADE (ORGANIZADOS) ---
    data_apresentacao = fields.Datetime(string='Apresentação', default=fields.Datetime.now, required=True, readonly=True)
    user_criacao_id = fields.Many2one('res.users', string='Criado Por', default=lambda self: self.env.user, readonly=True)
    
    validacao_datetime = fields.Datetime(string='Data Validação', readonly=True)
    validacao_user_id = fields.Many2one('res.users', string='Validado Por', readonly=True)
    
    data_entrada_patio = fields.Datetime(string='Entrada', readonly=True)
    entrada_user_id = fields.Many2one('res.users', string='Entrada Registrada Por', readonly=True)
    
    data_inicio_operacao = fields.Datetime(string='Início Operação', readonly=True)
    data_fim_operacao = fields.Datetime(string='Fim Operação', readonly=True)

    monitoramento_datetime = fields.Datetime(string='Monitoramento', readonly=True)
    monitoramento_user_id = fields.Many2one('res.users', string='Monitorado Por', readonly=True)

    data_conclusao = fields.Datetime(string='Saída', readonly=True) # Apenas uma definição
    conclusao_user_id = fields.Many2one('res.users', string='Concluído Por', readonly=True)
    
    # --- OUTROS CAMPOS ---
    current_location_id = fields.Many2one('stock.location', string='Localização Veículo', help="Local onde o veículo está fisicamente.", tracking=True)
    tipo_operacao_geral = fields.Selection([
        ('inbound', 'Entrada/Inbound'), ('outbound', 'Saída/Outbound'), ('in_out', 'Ent/In E Sai/Out'),
    ], string='Tipo Geral da Operação', required=True, default='outbound')

    motorista_id = fields.Many2one('res.partner', string='Motorista', required=True, domain="[('is_motorist', '=', True)]", tracking=True) 
    cavalo_id = fields.Many2one('lusitana_logistics.vehicle', string='Cavalo Mecânico', required=True, domain="[('tipo_frota', 'in', ['tracao', 'completo'])]", tracking=True)
    implemento_ids = fields.One2many('lusitana_logistics.vehicle_presentation_implement_line', 'presentation_id', string='Implementos', tracking=True)
    total_eixos = fields.Integer(string='Total de Eixos do Conjunto', compute='_compute_total_eixos', store=True)
    operation_summary = fields.Char(string='Resumo das Operações', compute='_compute_operation_summary')

    operation_line_ids = fields.One2many('lusitana_logistics.operation_line', 'presentation_id', string='Operações a Realizar')
    lacre_ids = fields.One2many('lusitana_logistics.vehicle_presentation_lacre_line', 'presentation_id', string='Lacres Utilizados', tracking=True)
    lacre_armador_manual = fields.Char(string='Número Lacre Armador (Manual)')
    necessita_lacres = fields.Boolean(string='Necessita Lacres?', compute='_compute_necessita_lacres', store=True)
    
    checklist_ids = fields.One2many('lusitana_logistics.vehicle_presentation_checklist', 'presentation_id', string='Checklists Realizados')
    checklist_count = fields.Integer(compute='_compute_checklist_count', string="Nº de Checklists")

    # --- NOVOS CAMPOS PARA CÁLCULO DE OTIF ---
    kpi_is_on_time = fields.Boolean(string="Chegou na Hora?", compute="_compute_kpi_otif", store=True, readonly=True)
    kpi_is_in_full = fields.Boolean(string="Carga Completa?", compute="_compute_kpi_otif", store=True, readonly=True)
    kpi_tempo_no_patio = fields.Float(string="Tempo no Pátio (Horas)", compute="_compute_kpi_otif", store=True, readonly=True)
    
    _sql_constraints = [('name_uniq', 'unique (name)', 'A referência da apresentação deve ser única!')]

    # --- MÉTODOS DE AÇÃO COM LÓGICA DE RASTREABILIDADE ---
    def action_validar(self):
        self.ensure_one()
        
        # --- NOVA VALIDAÇÃO ADICIONADA AQUI ---
        if not self.tipo_operacao_geral:
            raise ValidationError("É necessário selecionar o 'Tipo Geral da Operação' (Inbound, Outbound, etc.) antes de validar.")
        # --- FIM DA NOVA VALIDAÇÃO ---

        if not self.operation_line_ids:
            raise ValidationError("É necessário adicionar pelo menos uma linha de operação para validar.")
        
        # ... (lógica de validação do checklist de contêiner) ...
        
        self.operation_line_ids.write({'state': 'pendente'})
        self.write({
            'state': 'aguardando',
            'validacao_datetime': fields.Datetime.now(),
            'validacao_user_id': self.env.user.id
        })
    
    def action_registrar_entrada(self):
        self.ensure_one() # Garante que estamos trabalhando em um único registro

        # --- A TRAVA DE SEGURANÇA QUE FALTAVA ---
        if self.state != 'aguardando':
            raise ValidationError(_("A entrada só pode ser registrada para apresentações com status 'Aguardando'."))
        # --- FIM DA TRAVA ---

        self.write({
            'state': 'entrada', 
            'data_entrada_patio': fields.Datetime.now(),
            'entrada_user_id': self.env.user.id
        })
        
    def action_enviar_monitoramento(self):
        self.ensure_one()
        if self.state != 'ato':
             raise ValidationError("A apresentação precisa estar 'Aguardando ATO' para ser enviada ao monitoramento.")
        self.write({'state': 'monitoramento'})

    def action_aprovar_monitoramento(self):
        self.ensure_one()
        if self.state != 'monitoramento':
             raise ValidationError("A apresentação precisa estar em 'Monitoramento' para ser aprovada.")
        self.lacre_ids.mapped('lacre_id').filtered(lambda l: l.status == 'em_uso').write({'status': 'utilizado'})
        self.write({
            'state': 'concluido', 
            'data_conclusao': fields.Datetime.now(),
            'monitoramento_datetime': fields.Datetime.now(),
            'monitoramento_user_id': self.env.user.id,
            'conclusao_user_id': self.env.user.id
        })
    
    # --- RESTANTE DE TODOS OS MÉTODOS (CREATE, WRITE, COMPUTES, ETC.) ---
    # (O código abaixo é o restante dos métodos que já tínhamos, apenas para garantir que tudo está no lugar)
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == 'Novo':
                vals['name'] = self.env['ir.sequence'].next_by_code('lusitana_logistics.vehicle_presentation') or _('Erro de Sequência')
        presentations = super().create(vals_list)
        for presentation in presentations:
            if presentation.lacre_ids:
                presentation.lacre_ids.mapped('lacre_id').write({'status': 'em_uso', 'apresentacao_id': presentation.id})
        return presentations

    def write(self, vals):
        if 'lacre_ids' in vals:
            lacres_antes = self.lacre_ids.mapped('lacre_id')
            res = super().write(vals)
            lacres_depois = self.lacre_ids.mapped('lacre_id')
            lacres_removidos = lacres_antes - lacres_depois
            if lacres_removidos:
                lacres_removidos.write({'status': 'disponivel', 'apresentacao_id': False})
            lacres_adicionados = lacres_depois - lacres_antes
            if lacres_adicionados:
                if any(lacre.status != 'disponivel' for lacre in lacres_adicionados):
                    raise ValidationError("Um ou mais lacres selecionados já não estão mais disponíveis.")
                lacres_adicionados.write({'status': 'em_uso', 'apresentacao_id': self.id})
            return res
        return super().write(vals)

    @api.depends('checklist_ids')
    def _compute_checklist_count(self):
        for rec in self:
            rec.checklist_count = len(rec.checklist_ids)

    @api.depends('operation_line_ids.operation_type_id.name')
    def _compute_operation_summary(self):
        for rec in self:
            rec.operation_summary = ', '.join(rec.operation_line_ids.mapped('operation_type_id.name')) or 'Nenhuma operação definida'

    @api.depends('cavalo_id.qtde_eixos', 'implemento_ids.qtde_eixos_implemento')
    def _compute_total_eixos(self):
        for rec in self:
            rec.total_eixos = (rec.cavalo_id.qtde_eixos or 0) + sum(rec.implemento_ids.mapped('qtde_eixos_implemento'))

    @api.depends('operation_line_ids.prioridade_carregamento_id.is_priority_client', 'operation_line_ids.cliente_id')
    def _compute_necessita_lacres(self):
        for rec in self:
            # A lógica de 'ATACADÃO' permanece
            if any(line.cliente_id and 'ATACADÃO' in line.cliente_id.name.upper() for line in rec.operation_line_ids):
                rec.necessita_lacres = True
                continue

            # A nova lógica checa o campo booleano do cadastro de prioridade
            rec.necessita_lacres = any(line.prioridade_carregamento_id.is_priority_client for line in rec.operation_line_ids)
    
    def action_cancelar(self):
        self.ensure_one()
        self.lacre_ids.mapped('lacre_id').filtered(lambda l: l.status == 'em_uso').write({'status': 'disponivel', 'apresentacao_id': False})
        self.write({'state': 'cancelado'})

    def action_reset_to_draft(self):
        self.ensure_one()
        self.lacre_ids.mapped('lacre_id').filtered(lambda l: l.status == 'em_uso').write({'status': 'disponivel', 'apresentacao_id': False})
        self.write({'state': 'rascunho'})

    def _update_presentation_state(self):
        for presentation in self:
            if presentation.state in ['concluido', 'cancelado']:
                continue
            if not presentation.operation_line_ids:
                presentation.state = 'aguardando'
                continue
            line_states = set(presentation.operation_line_ids.mapped('state'))
            if all(s in ['concluida', 'cancelada'] for s in line_states):
                if presentation.state != 'ato':
                    presentation.write({'state': 'ato', 'data_fim_operacao': fields.Datetime.now()})
            elif 'em_andamento' in line_states:
                if presentation.state != 'em_operacao':
                    presentation.write({'state': 'em_operacao', 'data_inicio_operacao': fields.Datetime.now()})
            elif 'pendente' in line_states and 'em_andamento' not in line_states:
                presentation.state = 'entrada'

    def print_report_button(self):
        self.ensure_one()
        return self.env.ref('lusitana_logistics.action_report_vehicle_presentation').report_action(self)
        
    def action_open_checklists(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'name': _('Checklists da Apresentação'),
            'res_model': 'lusitana_logistics.vehicle_presentation_checklist',
            'domain': [('presentation_id', '=', self.id)],
            'context': {'default_presentation_id': self.id},
        }
        if self.checklist_ids:
            action['view_mode'] = 'list,form'
            if len(self.checklist_ids) == 1:
                action['res_id'] = self.checklist_ids.id
                action['view_mode'] = 'form'
        else:
            action.update({
                'name': _('Gerar Novo Checklist a partir de um Modelo'),
                'res_model': 'lusitana_logistics.checklist_generator_wizard',
                'view_mode': 'form',
                'target': 'new',
            })
        return action

    def action_print_zebra_label(self):
        self.ensure_one()
        zpl_string = self.env['ir.qweb']._render('lusitana_logistics.zpl_template_driver_badge',{'o': self})
        zpl_bytes = zpl_string.encode('utf-8')
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}_etiqueta.zpl',
            'datas': base64.b64encode(zpl_bytes),
            'mimetype': 'text/plain',
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    @api.depends('state', 'data_entrada_patio', 'operation_line_ids.dt_documento', 'operation_line_ids.state')
    def _compute_kpi_otif(self):
        for rec in self:
            rec.kpi_is_on_time = False
            rec.kpi_is_in_full = False
            rec.kpi_tempo_no_patio = 0.0

            # Só calcula KPIs para operações concluídas
            if rec.state == 'concluido':
                # --- CÁLCULO DO "ON TIME" ---
                # Pega a primeira linha de operação outbound para achar a agenda
                first_op = rec.operation_line_ids.filtered(lambda l: l.direction == 'outbound' and l.dt_documento)
                if first_op:
                    agenda = self.env['lusitana_logistics.agenda_heineken'].search([('dt_documento', '=', first_op[0].dt_documento)], limit=1)
                    if agenda and agenda.data_agendamento and rec.data_entrada_patio:
                        # Aqui definimos a regra de "On Time". 
                        # Ex: Chegou no mesmo dia da agenda? (Podemos refinar com a hora depois)
                        if rec.data_entrada_patio.date() == agenda.data_agendamento:
                            rec.kpi_is_on_time = True
                
                # --- CÁLCULO DO "IN FULL" ---
                # Verifica se TODAS as operações foram concluídas corretamente
                in_full = True
                for op_line in rec.operation_line_ids.filtered(lambda l: l.agenda_line_ids):
                    for agendado in op_line.agenda_line_ids:
                        qtd_conferida = len(op_line.conferencia_item_ids.filtered(lambda i: i.product_id == agendado.product_id))
                        if int(qtd_conferida) != int(agendado.quantidade):
                            in_full = False
                            break
                    if not in_full:
                        break
                rec.kpi_is_in_full = in_full

                # --- CÁLCULO DO TEMPO DE PÁTIO ---
                if rec.data_entrada_patio and rec.data_conclusao:
                    delta = rec.data_conclusao - rec.data_entrada_patio
                    rec.kpi_tempo_no_patio = delta.total_seconds() / 3600.0 # Resultado em horas