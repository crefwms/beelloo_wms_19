# -*- coding: utf-8 -*-
# models/lacre.py

from odoo import models, fields, api
from datetime import datetime

class Lacre(models.Model):
    _name = 'lusitana_logistics.lacre'
    _description = 'Controle de Lacres'
    _rec_name = 'name' 

    name = fields.Char(string='Número do Lacre', required=True, copy=False, index=True) 
    
    tipo_lacre = fields.Selection([
        ('hnk', 'Heineken (HNK)'),
        ('armador', 'Armador (Externo)'),
        ('outro', 'Outro'),
    ], string='Tipo de Lacre', required=True, default='hnk')

    status = fields.Selection([
        ('disponivel', 'Disponível'),
        ('em_uso', 'Em Uso'),
        ('utilizado', 'Utilizado'),
        ('danificado', 'Danificado'),
        ('perdido', 'Perdido'),
    ], string='Status', default='disponivel', required=True)

    fornecedor_id = fields.Many2one('res.partner', string='Fornecedor')
    data_recebimento = fields.Date(string='Data de Recebimento')

    data_atribuicao = fields.Datetime(string='Data de Atribuição') 
    user_atribuicao_id = fields.Many2one('res.users', string='Atribuído Por') 
    apresentacao_id = fields.Many2one(
        'lusitana_logistics.vehicle_presentation', 
        string='Vinculado à Apresentação'
    )

    observacoes = fields.Text(string='Observações')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Este número de lacre já está cadastrado!")
    ]

    @api.onchange('tipo_lacre')
    def _onchange_tipo_lacre(self):
        if self.tipo_lacre == 'armador':
            self.status = 'disponivel' 
        if self.status in ['disponivel', 'danificado', 'perdido']:
            self.data_atribuicao = False
            self.user_atribuicao_id = False
            self.apresentacao_id = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'status' not in vals:
                vals['status'] = 'disponivel'
            if 'data_atribuicao' not in vals and 'user_atribuicao_id' not in vals:
                vals['data_atribuicao'] = False
                vals['user_atribuicao_id'] = False
        return super().create(vals_list)

    def write(self, vals):
        # Se estamos atualizando o status
        if 'status' in vals:
            # Percorremos cada lacre no recordset (self)
            for lacre in self:
                # E aplicamos a lógica individualmente
                if vals['status'] in ['em_uso', 'utilizado'] and not lacre.data_atribuicao:
                    # Usamos um novo dicionário para o super() não receber o 'lacre'
                    update_vals = vals.copy()
                    update_vals['data_atribuicao'] = datetime.now()
                    update_vals['user_atribuicao_id'] = self.env.user.id
                    super(Lacre, lacre).write(update_vals)
                else:
                    super(Lacre, lacre).write(vals)
            return True
        
        return super().write(vals)
