# -*- coding: utf-8 -*-
# wizards/lacre_batch_wizard.py

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class LacreBatchWizard(models.TransientModel):
    _name = 'lusitana_logistics.lacre_batch_wizard'
    _description = 'Wizard de Entrada de Lacres em Lote'

    lacre_inicial = fields.Char(string='Lacre Inicial', required=True, help="Primeiro número do lacre da sequência.")
    lacre_final = fields.Char(string='Lacre Final', required=True, help="Último número do lacre da sequência.")
    tipo_lacre = fields.Selection([
        ('hnk', 'Heineken (HNK)'),
        ('armador', 'Armador'),
        ('outro', 'Outro')
    ], string='Tipo de Lacre', default='hnk', required=True)

    @api.constrains('lacre_inicial', 'lacre_final')
    def _check_lacre_sequence(self):
        for rec in self:
            if rec.lacre_inicial and rec.lacre_final:
                try:
                    num_inicial = int(rec.lacre_inicial)
                    num_final = int(rec.lacre_final)
                    if num_inicial >= num_final:
                        raise ValidationError(_("O número do Lacre Inicial deve ser menor que o Lacre Final."))
                except ValueError:
                    raise ValidationError(_("Os campos Lacre Inicial e Lacre Final devem conter apenas números para gerar a sequência."))

    def action_generate_lacres(self):
        self.ensure_one()
        lacre_obj = self.env['lusitana_logistics.lacre']
        
        num_inicial = int(self.lacre_inicial)
        num_final = int(self.lacre_final)
        
        lacres_to_create = []
        existing_lacres = lacre_obj.search([('name', '>=', self.lacre_inicial), ('name', '<=', self.lacre_final)]).mapped('name')

        for i in range(num_inicial, num_final + 1):
            lacre_name = str(i)
            if lacre_name not in existing_lacres:
                lacres_to_create.append({
                    'name': lacre_name,
                    'tipo_lacre': self.tipo_lacre,
                    'status': 'disponivel',
                })
        
        if lacres_to_create:
            lacre_obj.create(lacres_to_create)
            
            # Mensagem de sucesso
            message = _(f"Foram criados {len(lacres_to_create)} lacres com sucesso. ")
            if existing_lacres:
                message += _(f"({len(existing_lacres)} lacres da sequência já existiam e foram ignorados).")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Lacres Gerados'),
                    'message': message,
                    'type': 'success',
                    'sticky': False, # A notificação some após alguns segundos
                }
            }
        else:
            raise ValidationError(_("Nenhum lacre novo foi gerado, pois todos já existem na sequência ou a sequência é inválida."))