# -*- coding: utf-8 -*-
# models/priority.py

from odoo import models, fields

class Priority(models.Model):
    _name = 'lusitana_logistics.priority'
    _description = 'Cadastro de Prioridade de Carregamento'
    _order = 'sequence, name'

    name = fields.Char(string='Nome da Prioridade', required=True, 
                       help="Nome amigável da prioridade. Ex: 'TOP21', 'Perca de Agenda'")
    
    sap_code = fields.Char(string='Código SAP', required=True, index=True,
                           help="O texto EXATO que vem do SAP (Ex: 'TOP21', 'PERCA DE AGENDA', 'Gold')")
    
    sequence = fields.Integer(string='Sequência', default=10)
    
    is_priority_client = fields.Boolean(
        string="Cliente Prioritário?", 
        help="Marque esta opção se esta prioridade (Ex: TOP21, Diamante) "
             "exige tratamento especial, como a necessidade de lacres."
    )

    urgency_level = fields.Selection(
        [
            ('0', '0 - Crítica / Imediata (Tratar antes do agendamento)'),
            ('1', '1 - Alta (Tratar até o agendamento)'),
            ('2', '2 - Média (Tratar depois do agendamento)'),
            ('3', '3 - Baixa (Tratar conforme disponibilidade)'),
        ], 
        string="Nível de Urgência", 
        default='3',
        required=True
    )

    direction = fields.Selection(
        [
            ('inbound', 'Entrada/Inbound'), 
            ('outbound', 'Saída/Outbound')
        ], 
        string="Sentido da Operação", 
        help="Deixe em branco se esta prioridade se aplica a ambos os sentidos.",
        required=True
    )

    _sql_constraints = [
        ('sap_code_uniq', 'unique(sap_code)', 'Este código SAP já está cadastrado!')
    ]