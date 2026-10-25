from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging
import io
import hashlib
from datetime import datetime
from PIL import Image

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    cv2 = None
    np = None
    HAS_CV2 = False

_logger = logging.getLogger(__name__)


class TosignDocument(models.Model):
    _name = 'tosign.document'
    _description = 'Documento para Assinatura'
    _order = 'create_date desc'

    name = fields.Char(string='Nome do Documento', required=True)
    file = fields.Binary(string='Arquivo', attachment=True, required=True)
    file_name = fields.Char(string='Nome do Arquivo')
    file_type = fields.Selection([
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('doc', 'DOC'),
    ], string='Tipo de Arquivo', compute='_compute_file_type', store=True)

    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('pending', 'Pendente de Assinatura'),
        ('signed', 'Assinado'),
        ('cancelled', 'Cancelado'),
    ], string='Status', default='draft', tracking=True)

    signature_image = fields.Binary(string='Imagem da Assinatura', attachment=True)
    rubric_image = fields.Binary(string='Imagem da Rúbrica', attachment=True)

    has_signature = fields.Boolean(string='Possui Assinatura', default=False)
    has_rubric = fields.Boolean(string='Possui Rúbrica', default=False)

    signed_by = fields.Many2one('res.users', string='Assinado por', readonly=True)
    signed_date = fields.Datetime(string='Data da Assinatura', readonly=True)

    # Campos para auditoria
    document_hash = fields.Char(string='Hash do Documento Original', readonly=True)
    signature_metadata = fields.Text(string='Metadados da Assinatura', readonly=True)

    partner_id = fields.Many2one('res.partner', string='Partner')
    description = fields.Text(string='Descrição')

    @api.depends('file_name')
    def _compute_file_type(self):
        for record in self:
            if record.file_name:
                ext = record.file_name.split('.')[-1].lower()
                if ext == 'pdf':
                    record.file_type = 'pdf'
                elif ext == 'docx':
                    record.file_type = 'docx'
                elif ext == 'doc':
                    record.file_type = 'doc'
                else:
                    record.file_type = False
            else:
                record.file_type = False

    def action_pending(self):
        self.write({'state': 'pending'})

    def action_sign(self):
        self.ensure_one()
        _logger.info("Iniciando processo de assinatura para o documento: %s (Tipo: %s)", self.name, self.file_type)

        # Garantir que o file_type esteja computado
        if not self.file_type:
            self._compute_file_type()

        if self.file_type == 'pdf' and (self.signature_image or self.rubric_image):
            _logger.info("Condições atendidas. Gerando PDF assinado...")
            self._generate_signed_pdf()
        else:
            _logger.warning("PDF não gerado. file_type: %s, tem_assinatura: %s, tem_rubrica: %s",
                           self.file_type, bool(self.signature_image), bool(self.rubric_image))

        self.write({
            'state': 'signed',
            'signed_by': self.env.user.id,
            'signed_date': fields.Datetime.now(),
        })

    def _generate_signed_pdf(self):
        """
        Gera um novo PDF com campo de assinatura interativo (como DocuSign).
        Adiciona annotation de assinatura com imagem, nome, data e hash.
        """
        self.ensure_one()
        if not HAS_FITZ:
            raise UserError("PyMuPDF (fitz) não está instalado. Execute: pip install pymupdf")

        try:
            # Abrir PDF com PyMuPDF
            original_pdf_data = base64.b64decode(self.file)
            doc = fitz.open("pdf", original_pdf_data)

            # Calcular hash do documento original (SHA-256)
            original_hash = hashlib.sha256(original_pdf_data).hexdigest()[:16]  # Primeiros 16 chars

            # Processar cada página
            for page_num in range(len(doc)):
                page = doc[page_num]

                # Aplicar rúbrica em TODAS as páginas (como stamp simples)
                if self.has_rubric:
                    self._add_rubric_stamp(page)

                # Aplicar assinatura apenas na ÚLTIMA página
                if self.has_signature and page_num == len(doc) - 1:
                    self._add_signature_field(
                        page,
                        self.signature_image,
                        signer_name=self.env.user.name,
                        sign_date=fields.Datetime.now(),
                        doc_hash=original_hash
                    )

            # Salvar PDF modificado
            output_stream = io.BytesIO()
            doc.save(output_stream)
            doc.close()

            signed_pdf_data = base64.b64encode(output_stream.getvalue())

            new_file_name = self.file_name or 'documento'
            if not new_file_name.lower().endswith('_assinado.pdf'):
                name_parts = new_file_name.rsplit('.', 1)
                new_file_name = f"{name_parts[0]}_assinado.pdf"

            # Salvar hash e metadados para auditoria
            metadata = {
                'original_hash': original_hash,
                'signed_by': self.env.user.id,
                'signed_by_name': self.env.user.name,
                'signed_date': fields.Datetime.now().isoformat(),
                'has_signature': self.has_signature,
                'has_rubric': self.has_rubric,
            }

            self.write({
                'file': signed_pdf_data,
                'file_name': new_file_name,
                'document_hash': original_hash,
                'signature_metadata': str(metadata),
            })

            _logger.info("PDF assinado com sucesso. Hash: %s", original_hash)

        except Exception as e:
            _logger.error("Erro ao gerar PDF assinado: %s", str(e), exc_info=True)
            raise UserError(f"Erro ao processar PDF: {str(e)}")

    def _add_rubric_stamp(self, page):
        """
        Adiciona rúbrica como stamp simples em cada página.
        """
        img_binary = base64.b64decode(self.rubric_image)

        # Redimensionar e preparar imagem
        img = self._prepare_image(img_binary, max_width=100, max_height=50)

        # Posição: canto inferior direito
        pos_x = page.rect.width - 120
        pos_y = 20

        # Criar rectangle para a imagem
        rect = fitz.Rect(pos_x, pos_y, pos_x + img.width, pos_y + img.height)

        # Inserir imagem
        page.insert_image(rect, pixmap=img)

    def _add_signature_field(self, page, signature_image, signer_name, sign_date, doc_hash):
        """
        Adiciona uma área de assinatura visual na última página.
        Cria um estampa (stamp) com: imagem, nome, data, hash e borda.
        """
        img_binary = base64.b64decode(signature_image)

        # Preparar imagem da assinatura
        sig_img = self._prepare_image(img_binary, max_width=200, max_height=100, return_pil=True)

        # Criar canvas para a área completa da assinatura
        from PIL import ImageDraw, ImageFont

        margin = 15
        text_height = 60  # espaço para nome, data e hash
        canvas_width = sig_img.width + (margin * 2)
        canvas_height = sig_img.height + text_height + (margin * 2)

        # Criar canvas branco
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        # Desenhar borda
        draw.rectangle([0, 0, canvas_width-1, canvas_height-1], outline=(0, 0, 0), width=2)

        # Posicionar imagem da assinatura
        img_x = margin
        img_y = margin
        canvas.paste(sig_img, (img_x, img_y), sig_img)

        # Adicionar texto
        try:
            font = ImageFont.load_default()
        except:
            font = None

        text_x = img_x + sig_img.width + 10
        text_y = img_y + 5

        # Nome do signatário
        draw.text((text_x, text_y), f"Assinado por: {signer_name}", fill=(0, 0, 0), font=font)

        # Data
        draw.text((text_x, text_y + 20), f"Data: {sign_date.strftime('%d/%m/%Y %H:%M')}", fill=(0, 0, 0), font=font)

        # Hash (pequeno)
        draw.text((text_x, text_y + 35), f"Hash: {doc_hash}", fill=(100, 100, 100), font=font)

        # Converter para Pixmap
        img_bytes = io.BytesIO()
        canvas.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        appearance_pix = fitz.Pixmap(img_bytes.getvalue())

        # Posicionar no centro inferior da página
        pos_x = (page.rect.width - canvas_width) / 2
        pos_y = 50
        rect = fitz.Rect(pos_x, pos_y, pos_x + canvas_width, pos_y + canvas_height)

        # Adicionar como imagem na página
        page.insert_image(rect, pixmap=appearance_pix)

        # Adicionar annotation invisível com metadados para auditoria (se necessário no futuro)
        # Isso permite extrair informações do PDF posteriormente
        try:
            annot = page.add_text_annot(fitz.Point(pos_x, pos_y),
                                       text=f"ToSign Signature\nSigner: {signer_name}\nDate: {sign_date.isoformat()}\nHash: {doc_hash}")
            annot.set_colors(stroke=(1, 1, 1))  # Branco (invisível)
            annot.set_border(width=0)
            annot.update()
        except Exception as e:
            _logger.warning("Não foi possível adicionar a annotation de auditoria: %s", str(e))

        _logger.info("Assinatura visual adicionada para %s em (%.0f, %.0f)", signer_name, pos_x, pos_y)

    def _create_signature_appearance(self, sig_img, signer_name, sign_date, doc_hash, width, height):
        """
        Cria uma appearance (visual) para o campo de assinatura.
        Retorna um Pixmap com a imagem completa: assinatura + texto + hash.
        """
        # Dimensões
        margin = 10
        text_height = 40
        hash_height = 20
        total_height = int(height)

        # Criar canvas (imagem maior para conter assinatura + texto)
        canvas_height = sig_img.height + text_height + hash_height + (margin * 2)
        canvas_width = int(width) - (margin * 2)

        # Criar imagem base (fundo branco)
        canvas = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 255))
        # Importar draw para texto
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(canvas)

        # Colar imagem da assinatura no topo
        sig_y = margin
        canvas.paste(sig_img, (margin, sig_y), sig_img)

        # Adicionar texto: nome e data
        try:
            # Tentar usar uma fonte padrão
            font = ImageFont.load_default()
        except:
            font = None

        text_y = sig_y + sig_img.height + 5
        draw.text((margin, text_y), f"Assinado por: {signer_name}", fill=(0, 0, 0), font=font)
        draw.text((margin, text_y + 15), f"Data: {sign_date.strftime('%d/%m/%Y %H:%M')}", fill=(0, 0, 0), font=font)

        # Adicionar hash (pequeno)
        hash_text = f"Hash: {doc_hash}"
        draw.text((margin, text_y + 30), hash_text, fill=(100, 100, 100), font=font)

        # Adicionar borda ao redor
        from PIL import ImageDraw
        draw_border = ImageDraw.Draw(canvas)
        draw_border.rectangle([0, 0, canvas_width-1, canvas_height-1], outline=(0, 0, 0), width=2)

        # Converter para Pixmap do PyMuPDF
        img_bytes = io.BytesIO()
        canvas.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return fitz.Pixmap(img_bytes.getvalue())

    def _prepare_image(self, img_binary, max_width, max_height, return_pil=False):
        """
        Prepara imagem (redimensiona e converte para Pixmap ou retorna PIL Image).
        """
        try:
            img = Image.open(io.BytesIO(img_binary))
            img.load()
        except Exception as e:
            if HAS_CV2:
                arr = np.frombuffer(img_binary, dtype=np.uint8)
                cv_img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)
                if cv_img is None:
                    raise UserError(f"Não foi possível decodificar a imagem.")
                if cv_img.ndim == 3:
                    if cv_img.shape[2] == 4:
                        img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA))
                    else:
                        img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
                else:
                    img = Image.fromarray(cv_img)
            else:
                raise UserError(f"Erro ao processar imagem: {str(e)}")

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Redimensionar mantendo proporção
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        if return_pil:
            return img

        # Converter para Pixmap
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)

        return fitz.Pixmap(img_bytes.getvalue())

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
