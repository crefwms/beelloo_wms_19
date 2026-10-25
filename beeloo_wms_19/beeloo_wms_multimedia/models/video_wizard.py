from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BeelooVideoWizard(models.TransientModel):
    _name = 'beeloo.video.wizard'
    _description = 'Assistente de Captura de Evidência'

    # Campos de ligação (Quem chamou o wizard?)
    # Se você ainda não tem o módulo beeloo.presentation instalado, 
    # comente a linha abaixo para não dar erro de "Model not found"
    presentation_id = fields.Many2one('beeloo.presentation', string="Portaria")
    
    picking_id = fields.Many2one('stock.picking', string="Operação (Picking)")

    # O Arquivo
    evidence_file = fields.Binary(string="Arquivo de Mídia", required=True, attachment=False)
    filename = fields.Char(string="Nome do Arquivo")
    note = fields.Text(string="Observação")

    def action_save_evidence(self):
        self.ensure_one()
        
        # 1. Define quem é o dono do vídeo
        target_record = self.picking_id or self.presentation_id
        if not target_record:
            # Fallback seguro caso abra o wizard sem contexto
            raise UserError(_("Erro: Nenhuma operação vinculada."))

        # 2. Cria o anexo oficial
        attachment = self.env['ir.attachment'].create({
            'name': self.filename or f"evidencia_{target_record.name}.mp4",
            'type': 'binary',
            'datas': self.evidence_file,
            'res_model': target_record._name,
            'res_id': target_record.id,
            'mimetype': 'video/mp4', 
        })

        # 3. Tenta vincular ao campo x_document_ids se ele existir
        if hasattr(target_record, 'x_document_ids'):
            target_record.write({
                'x_document_ids': [(4, attachment.id)]
            })
        
        return {'type': 'ir.actions.act_window_close'}