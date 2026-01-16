from odoo import http
from odoo.http import request

class WmsPresentation(http.Controller):

    # Rota para exibir a página inicial E processar a busca
    @http.route(['/wms/info', '/wms/tracking'], type='http', auth="public", website=True)
    def wms_landing(self, ref_number=None, **kwargs):
        picking = False
        
        # Se o usuário digitou algo (ref_number veio do formulário)
        if ref_number:
            # .sudo() é usado aqui para permitir que visitantes (sem login) busquem
            # CUIDADO: Em produção, filtramos melhor para não expor tudo.
            picking = request.env['stock.picking'].sudo().search([
                ('name', 'ilike', ref_number)
            ], limit=1)

        return request.render('beeloo_wms_presentation.landing_page', {
            'picking': picking,       # Passamos o objeto encontrado (ou vazio)
            'search_term': ref_number # Passamos o que foi digitado para mostrar na tela
        })