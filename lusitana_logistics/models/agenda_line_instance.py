# -*- coding: utf-8 -*-
# models/agenda_line_instance.py

from odoo import models, fields, api, _
import logging
_logger = logging.getLogger(__name__)

RPM_CATEGORY_NAME = 'RPM'

class AgendaHeinekenLineInstance(models.Model):
    _name = 'lusitana_logistics.agenda_heineken_line_instance'
    _description = 'Instância de Linha de Produto da Agenda na Operação'

    operation_line_id = fields.Many2one('lusitana_logistics.operation_line', string='Linha de Operação', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Produto')
    quantidade = fields.Float(string='Qtd. Agendada (Unid)')
    quantidade_paletes = fields.Float(string='Qtd. Paletes')

    quantidade_conferida = fields.Float(string='Qtd. Conferida (Bips)', compute='_compute_conferencia_por_bip', store=True)
    quantidade_conferida_manual = fields.Float(string='Qtd. Conferida (Manual)', default=0.0)

    is_rpm = fields.Boolean(
        string="É RPM?",
        store=True,
        compute='_compute_is_rpm',
        readonly=True
    )

    @api.depends('product_id.categ_id')
    def _compute_is_rpm(self):
        """Define o campo is_rpm baseado no nome da categoria"""
        rpm_category = self.env['product.category'].search([('name', '=', RPM_CATEGORY_NAME)], limit=1)
        if not rpm_category:
             _logger.warning(f"Categoria de produto '{RPM_CATEGORY_NAME}' não encontrada para checagem is_rpm.")
             for record in self:
                 record.is_rpm = False
             return

        for record in self:
            record.is_rpm = bool(record.product_id and record.product_id.categ_id == rpm_category)


    @api.depends('operation_line_id.conferencia_item_ids.product_id', 'product_id')
    def _compute_conferencia_por_bip(self):
        if not self:
            return

        # Agrupa por operation_line_id para fazer menos buscas
        ops_data = self.env['lusitana_logistics.conferencia_item']._read_group(
            [('operation_line_id', 'in', self.operation_line_id.ids), ('product_id', 'in', self.product_id.ids)], # Otimiza mais ainda
            ['operation_line_id', 'product_id'],
            ['__count']
        )

        # Mapeia os dados para fácil acesso: {op_id: {prod_id: count}}
        count_map = {}
        for op, prod, count in ops_data:
            op_id = op[0]
            prod_id = prod[0] if prod else False
            if op_id not in count_map:
                count_map[op_id] = {}
            if prod_id:
                count_map[op_id][prod_id] = count

        # Aplica a contagem
        for record in self:
            # --- AQUI ESTAVA O ERRO ---
            # Acesso incorreto: count_map.get(record.product_id, 0.0)
            # --- CORREÇÃO ---
            # Acessa o mapa usando op_id e depois prod_id
            record.quantidade_conferida = count_map.get(record.operation_line_id.id, {}).get(record.product_id.id, 0)
            # --- FIM DA CORREÇÃO ---