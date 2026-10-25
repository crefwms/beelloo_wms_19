# -*- coding: utf-8 -*-
# wizards/checklist_generator_wizard.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ChecklistGeneratorWizard(models.TransientModel):
    _name = 'lusitana_logistics.checklist_generator_wizard'
    _description = 'Assistente para Gerar Checklist a partir de um Modelo'

    checklist_template_id = fields.Many2one(
        'lusitana_logistics.checklist_template',
        string='Modelo de Checklist',
        required=True,
        domain="[('active', '=', True)]"
    )

    def action_generate_and_open_checklist(self):
        self.ensure_one()
        presentation_id = self.env.context.get('active_id')
        presentation = self.env['lusitana_logistics.vehicle_presentation'].browse(presentation_id)
        
        existing_checklist = self.env['lusitana_logistics.vehicle_presentation_checklist'].search([
            ('presentation_id', '=', presentation.id),
            ('checklist_template_id', '=', self.checklist_template_id.id),
        ], limit=1)

        if existing_checklist:
            raise ValidationError(_("Já existe um checklist deste modelo para esta apresentação. Por favor, edite o existente ou escolha outro modelo."))
        
        # Cria o cabeçalho do checklist
        new_checklist = self.env['lusitana_logistics.vehicle_presentation_checklist'].create({
            'presentation_id': presentation.id,
            'checklist_template_id': self.checklist_template_id.id,
            'status': 'pendente',
        })

        # Cria as linhas de itens baseadas no modelo
        item_lines_to_create = []
        for item_template in self.checklist_template_id.item_ids:
            item_lines_to_create.append({
                'checklist_id': new_checklist.id,
                'item_template_id': item_template.id,
            })
        
        if item_lines_to_create:
            self.env['lusitana_logistics.vehicle_presentation_checklist_item'].create(item_lines_to_create)

        # Retorna a ação para abrir o formulário do checklist recém-criado
        return {
            'type': 'ir.actions.act_window',
            'name': _('Preencher Checklist'),
            'res_model': 'lusitana_logistics.vehicle_presentation_checklist',
            'view_mode': 'form',
            'res_id': new_checklist.id,
            'target': 'current', # Abre na mesma janela
        }