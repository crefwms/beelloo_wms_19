# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class BeelooLacreCreateBatch(models.TransientModel):
    _name = 'beeloo.lacre.create_batch'
    _description = 'Wizard: Criar Lacres em Lote'

    prefixo = fields.Char(string='Prefixo')
    numero_inicial = fields.Integer(string='Número Inicial', required=True, default=1)
    numero_final = fields.Integer(string='Número Final', required=True, default=1)
    padding = fields.Integer(
        string='Preenchimento (Zeros)', 
        default=4, 
        help="Ex: 4 -> 0001; 5 -> 00001"
    )
    
    # Campos para copiar para os lacres
    tipo_lacre = fields.Selection([
        ('hnk', 'Heineken (HNK)'),
        ('outro', 'Outro'),
    ], string='Tipo de Lacre', required=True, default='hnk')
    fornecedor_id = fields.Many2one('res.partner', string='Fornecedor')
    data_recebimento = fields.Date(string='Data de Recebimento', default=fields.Date.context_today)

    def action_create_lacres(self):
        self.ensure_one()
        if self.numero_final < self.numero_inicial:
            raise UserError('O número final deve ser maior ou igual ao número inicial.')
        
        if (self.numero_final - self.numero_inicial) > 10000: # Limite de segurança
             raise UserError('Você não pode criar mais de 10.000 lacres de uma vez.')

        lacre_model = self.env['beeloo.lacre']
        lacres_criados = []
        
        for num in range(self.numero_inicial, self.numero_final + 1):
            # Formata o número: ex: "0001"
            numero_formatado = str(num).zfill(self.padding)
            # Concatena prefixo: ex: "HNK-0001"
            nome_lacre = (self.prefixo or '') + numero_formatado

            lacres_criados.append({
                'name': nome_lacre,
                'tipo_lacre': self.tipo_lacre,
                'fornecedor_id': self.fornecedor_id.id,
                'data_recebimento': self.data_recebimento,
                'status': 'disponivel',
            })
        
        # Cria todos de uma vez (melhor performance)
        lacre_model.create(lacres_criados)
        
        return {'type': 'ir.actions.act_window_close'}