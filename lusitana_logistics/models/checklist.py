# -*- coding: utf-8 -*-
# models/checklist.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# --- 1. Modelo de Template de Checklist (Checklist Template) ---
class ChecklistTemplate(models.Model):
    _name = 'lusitana_logistics.checklist_template'
    _description = 'Modelo de Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Nome do Checklist', required=True, tracking=True)
    description = fields.Text(string='Descrição')
    active = fields.Boolean(string='Ativo', default=True)
    is_mandatory_for_container = fields.Boolean(string="Obrigatório para Contêiner?", help="Marque esta opção se este checklist for obrigatório para apresentações de veículos que sejam contêineres.")
    item_ids = fields.One2many('lusitana_logistics.checklist_item_template', 'checklist_template_id', string='Itens do Checklist')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'O nome do Checklist deve ser único!')
    ]

# --- 2. Modelo de Item de Template de Checklist (Checklist Item Template) ---
class ChecklistItemTemplate(models.Model):
    _name = 'lusitana_logistics.checklist_item_template'
    _description = 'Item do Modelo de Checklist'
    _order = 'sequence, id'

    name = fields.Char(string='Pergunta / Item de Verificação', required=True)
    sequence = fields.Integer(string='Sequência', default=10)
    checklist_template_id = fields.Many2one('lusitana_logistics.checklist_template', string='Modelo de Checklist', required=True, ondelete='cascade')
    
    answer_type = fields.Selection([
        ('boolean', 'Sim/Não (OK/Não OK)'),
        ('text', 'Texto Curto'),
        ('long_text', 'Texto Longo'),
        ('selection', 'Múltipla Escolha'),
        ('integer', 'Número Inteiro'),
        ('float', 'Número Decimal'),
    ], string='Tipo de Resposta', default='boolean', required=True)

    selection_options = fields.Char(string='Opções de Escolha', help="Separar as opções por vírgula (ex: 'Opção A, Opção B, Opção C')")
    is_critical = fields.Boolean(string='Crítico / Obrigatório', default=False)
    guidance = fields.Text(string='Orientação/Instrução')

    @api.constrains('selection_options', 'answer_type')
    def _check_selection_options(self):
        for rec in self:
            if rec.answer_type == 'selection' and not rec.selection_options:
                raise ValidationError(_("As opções de escolha são obrigatórias para o tipo de resposta 'Múltipla Escolha'."))

# --- 3. Modelo de Checklist da Apresentação ---
class VehiclePresentationChecklist(models.Model):
    _name = 'lusitana_logistics.vehicle_presentation_checklist'
    _description = 'Checklist Preenchido da Apresentação'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    presentation_id = fields.Many2one('lusitana_logistics.vehicle_presentation', string='Apresentação', required=True, ondelete='cascade', index=True)
    checklist_template_id = fields.Many2one('lusitana_logistics.checklist_template', string='Modelo de Checklist', required=True, ondelete='restrict')
    display_name = fields.Char(string='Nome do Checklist', compute='_compute_display_name', store=True)
    
    status = fields.Selection([
        ('pendente', 'Pendente'),
        ('em_preenchimento', 'Em Preenchimento'),
        ('concluido_ok', 'Concluído (OK)'),
        ('concluido_nok', 'Concluído (NÃO OK)'),
        ('cancelado', 'Cancelado'),
    ], string='Status', default='pendente', tracking=True, copy=False)

    start_time = fields.Datetime(string='Início Preenchimento', readonly=True)
    end_time = fields.Datetime(string='Fim Preenchimento', readonly=True)
    filled_by_id = fields.Many2one('res.users', string='Preenchido Por', readonly=True)

    item_line_ids = fields.One2many('lusitana_logistics.vehicle_presentation_checklist_item', 'checklist_id', string='Respostas', copy=True)
    has_critical_failures = fields.Boolean(string='Falhas Críticas?', compute='_compute_critical_failures', store=True)

    _sql_constraints = [
        ('presentation_template_uniq', 'unique (presentation_id, checklist_template_id)', 'Este modelo de checklist já foi usado para esta apresentação!')
    ]

    @api.depends('presentation_id.name', 'checklist_template_id.name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.presentation_id.name} - {rec.checklist_template_id.name}"

    @api.depends('item_line_ids.is_critical_item', 'item_line_ids.is_ok')
    def _compute_critical_failures(self):
        for rec in self:
            rec.has_critical_failures = any(item.is_critical_item and not item.is_ok for item in rec.item_line_ids)

    def action_start_filling(self):
        self.ensure_one()
        self.write({'status': 'em_preenchimento', 'start_time': fields.Datetime.now(), 'filled_by_id': self.env.user.id})
    
    def action_finish_filling(self):
        self.ensure_one()
        
        # 1. Verificar se todos os itens foram preenchidos (Opcional, mas recomendado)
        # 2. Avaliar falhas críticas
        if any(item.is_critical_item and not item.is_ok for item in self.item_line_ids):
            self.status = 'concluido_nok'
            # Aqui você pode disparar uma mensagem ou atividade para o gestor
        else:
            self.status = 'concluido_ok'
        
        self.end_time = fields.Datetime.now()

# --- 4. Modelo de Resposta de Item de Checklist ---
class VehiclePresentationChecklistItem(models.Model):
    _name = 'lusitana_logistics.vehicle_presentation_checklist_item'
    _description = 'Item de Resposta do Checklist'
    _order = 'sequence, id'

    checklist_id = fields.Many2one('lusitana_logistics.vehicle_presentation_checklist', string='Checklist', required=True, ondelete='cascade')
    item_template_id = fields.Many2one('lusitana_logistics.checklist_item_template', string='Item Template', required=True, ondelete='restrict')
    
    name = fields.Char(related='item_template_id.name', readonly=True)
    sequence = fields.Integer(related='item_template_id.sequence', readonly=True, store=True)
    answer_type = fields.Selection(related='item_template_id.answer_type', readonly=True)
    selection_options_str = fields.Char(related='item_template_id.selection_options', readonly=True)
    is_critical_item = fields.Boolean(related='item_template_id.is_critical', readonly=True)
    guidance = fields.Text(related='item_template_id.guidance', readonly=True)

    answer_boolean = fields.Boolean(string='Resposta (OK?)')
    answer_text = fields.Char(string='Resposta')
    answer_long_text = fields.Text(string='Resposta')
    answer_selection = fields.Selection(selection='_get_selection_options', string='Resposta') 
    answer_integer = fields.Integer(string='Resposta')
    answer_float = fields.Float(string='Resposta')

    is_ok = fields.Boolean(string='Está OK?', compute='_compute_is_ok', store=True)
    is_conforming = fields.Boolean(string='Conforme?', default=True)

    @api.depends('answer_type', 'answer_boolean', 'is_conforming', 
                 'answer_text', 'answer_integer', 'answer_float')
    def _compute_is_ok(self):
        for rec in self:
            if rec.answer_type == 'boolean':
                # Se for booleano, o OK é a própria resposta
                rec.is_ok = rec.answer_boolean
            else:
                # Se for texto/número, o OK depende do veredito manual do operador
                rec.is_ok = rec.is_conforming

    def _get_selection_options(self):
        if self.selection_options_str:
            return [(opt.strip(), opt.strip()) for opt in self.selection_options_str.split(',')]
        return []