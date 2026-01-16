# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DamageReportWizard(models.TransientModel):
    _name = 'beeloo.damage.report.wizard'
    _description = 'Assistente para Reportar Avaria no Recebimento'

    move_line_id = fields.Many2one(
        'stock.move.line', 
        string='Linha do Produto', 
        required=True, 
        readonly=True
    )
    product_id = fields.Many2one(related='move_line_id.product_id', readonly=True)
    lot_id = fields.Many2one(related='move_line_id.lot_id', readonly=True)

    # --- USANDO CAMPOS COMPUTADOS ---
    quantity_total = fields.Float(
        string="Quantidade Esperada", 
        compute='_compute_quantities',
        readonly=True
    )
    quantity_done_good = fields.Float(
        string="Quantidade Boa (Já bipada)", 
        compute='_compute_quantities',
        readonly=True
    )

    quantity_damaged = fields.Float(string="Quantidade Avariada", required=True)
    reason = fields.Text(string="Motivo da Avaria", required=True)
    damage_location_id = fields.Many2one(
        'stock.location', 
        string="Local de Destino (Avarias)", 
        required=True,
        domain="[('usage', '=', 'internal')]"
    )

    @api.depends('move_line_id')
    def _compute_quantities(self):
        for record in self:
            if record.move_line_id:
                # Tenta pegar a quantidade do move relacionado ou da própria linha
                record.quantity_total = record.move_line_id.move_id.product_uom_qty or 0.0
                record.quantity_done_good = record.move_line_id.qty_done or 0.0
            else:
                record.quantity_total = 0.0
                record.quantity_done_good = 0.0

    def action_confirm_damage(self):
        self.ensure_one()
        move_line = self.move_line_id
        picking = move_line.picking_id

        total_qty = self.quantity_done_good + self.quantity_damaged
        if total_qty > self.quantity_total:
            raise UserError(
                _("A soma da 'Quantidade Boa' (%(good)s) e 'Avariada' (%(dmg)s) não pode "
                  "exceder a 'Quantidade Esperada' (%(total)s).") % {
                    'good': self.quantity_done_good,
                    'dmg': self.quantity_damaged,
                    'total': self.quantity_total
                }
            )

        bo = self.env['beeloo.damage.report'].create({
            'picking_id': picking.id,
            'presentation_id': picking.x_presentation_id.id,
            'move_line_id': move_line.id,
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id,
            'quantity_damaged': self.quantity_damaged,
            'reason': self.reason,
            'state': 'pending',
        })

        new_move_line = move_line.copy({
            'move_id': move_line.move_id.id,
            'product_uom_qty': 0, 
            'qty_done': self.quantity_damaged,
            'location_id': move_line.location_id.id,
            'location_dest_id': self.damage_location_id.id,
            'state': 'assigned',
            'x_damage_report_id': bo.id,
        })

        if self.quantity_done_good == 0:
             move_line.qty_done = self.quantity_total - self.quantity_damaged

        picking.message_post(body=_(
            "Boletim de Ocorrência %(bo_name)s criado: %(dmg_qty)s un. de %(product)s movidas para %(loc)s.",
            bo_name=bo.name,
            dmg_qty=self.quantity_damaged,
            product=self.product_id.display_name,
            loc=self.damage_location_id.display_name
        ))
        return {'type': 'ir.actions.act_window_close'}