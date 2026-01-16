# -*- coding: utf-8 -*-
from odoo import models, fields

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    x_is_quarantine_type = fields.Boolean(
        string="É a Operação de Quarentena (Beeloo)?",
        help="Marque esta opção (em UMA operação de Mov. Interna) para definir "
             "que este é o destino padrão dos produtos vetados pelo CQ."
    )