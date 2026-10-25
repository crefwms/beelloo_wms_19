import base64
import logging
from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TosignController(http.Controller):

    @http.route('/tosign/upload', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_document(self):
        try:
            file = request.httprequest.files.get('file')
            if not file:
                return request.render('tosign_app.tosign_error', {
                    'error': 'Nenhum arquivo enviado'
                })
            
            filename = file.filename.lower()
            allowed_extensions = ['pdf', 'doc', 'docx']
            ext = filename.split('.')[-1] if '.' in filename else ''
            
            if ext not in allowed_extensions:
                return request.render('tosign_app.tosign_error', {
                    'error': f'Tipo de arquivo não permitido. Use: {", ".join(allowed_extensions)}'
                })
            
            file_content = base64.b64encode(file.read())
            
            doc = request.env['tosign.document'].create({
                'name': filename,
                'file': file_content,
                'file_name': filename,
                'state': 'draft',
            })
            
            return request.redirect(f'/web#id={doc.id}&model=tosign.document&view_type=form')
            
        except Exception as e:
            _logger.error(f'Erro ao fazer upload: {str(e)}')
            return request.render('tosign_app.tosign_error', {
                'error': f'Erro ao processar arquivo: {str(e)}'
            })

    @http.route('/tosign/sign/<int:document_id>', type='http', auth='user')
    def sign_document(self, document_id):
        doc = request.env['tosign.document'].browse(document_id)
        if not doc.exists():
            return request.render('tosign_app.tosign_error', {
                'error': 'Documento não encontrado'
            })
        
        return request.render('tosign_app.tosign_sign_page', {
            'document': doc,
            'document_id': document_id,
        })

    @http.route('/tosign/save_signature', type='json', auth='user', methods=['POST'])
    def save_signature(self, document_id, signature_data):
        try:
            doc = request.env['tosign.document'].browse(document_id)
            if not doc.exists():
                return {'success': False, 'error': 'Documento não encontrado'}
            
            if doc.state != 'pending':
                return {'success': False, 'error': 'Documento não está pendente de assinatura'}
            
            signature_image = signature_data.split(',')[-1]
            signature_binary = base64.b64decode(signature_image)
            
            doc.write({
                'signature_image': base64.b64encode(signature_binary),
                'state': 'signed',
                'signed_by': request.env.user.id,
                'signed_date': fields.Datetime.now(),
            })
            
            return {'success': True}
            
        except Exception as e:
            _logger.error(f'Erro ao salvar assinatura: {str(e)}')
            return {'success': False, 'error': str(e)}

    @http.route('/tosign/download/<int:document_id>', type='http', auth='user')
    def download_document(self, document_id):
        doc = request.env['tosign.document'].browse(document_id)
        if not doc.exists():
            return request.not_found()
        
        return request.make_response(
            base64.b64decode(doc.file),
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{doc.file_name}"'),
            ]
        )
