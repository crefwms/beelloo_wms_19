import base64
from odoo import fields, models, api
from odoo.exceptions import UserError


class TosignSignWizard(models.TransientModel):
    _name = 'tosign.sign.wizard'
    _description = 'Wizard para Assinar Documento'

    document_id = fields.Many2one('tosign.document', string='Documento', required=True)
    sign_mode = fields.Selection([
        ('both', 'Assinatura e Rúbrica'),
        ('sig', 'Apenas Assinatura'),
        ('rub', 'Apenas Rúbrica'),
    ], string='Modo de Assinatura', default='both', required=True)
    
    signature_source = fields.Selection([
        ('draw', 'Desenhar'),
        ('upload', 'Fazer Upload (Imagem)')
    ], string='Origem da Assinatura', default='draw', required=True)
    signature_image = fields.Binary(string='Desenhar Assinatura')
    signature_upload = fields.Binary(string='Upload da Assinatura')

    rubric_source = fields.Selection([
        ('draw', 'Desenhar'),
        ('upload', 'Fazer Upload (Imagem)')
    ], string='Origem da Rúbrica', default='draw', required=True)
    rubric_image = fields.Binary(string='Desenhar Rúbrica')
    rubric_upload = fields.Binary(string='Upload da Rúbrica')

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            res['document_id'] = active_id
        return res

    def action_sign(self):
        self.ensure_one()
        
        final_signature = self.signature_image if self.signature_source == 'draw' else self.signature_upload
        final_rubric = self.rubric_image if self.rubric_source == 'draw' else self.rubric_upload

        if self.sign_mode in ('both', 'sig') and not final_signature:
            raise UserError('A imagem da assinatura é obrigatória para este modo.')
        if self.sign_mode in ('both', 'rub') and not final_rubric:
            raise UserError('A imagem da rúbrica é obrigatória para este modo.')
        
        vals = {
            'has_signature': self.sign_mode in ('both', 'sig'),
            'has_rubric': self.sign_mode in ('both', 'rub'),
        }
        if vals['has_signature']:
            vals['signature_image'] = final_signature
        if vals['has_rubric']:
            vals['rubric_image'] = final_rubric

        # Salva as imagens e opções no documento
        self.document_id.write(vals)
        
        # Chama a ação que contém a lógica de processamento do PDF
        self.document_id.action_sign()
        
        return {'type': 'ir.actions.act_window_close'}
