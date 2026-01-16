# -*- coding: utf-8 -*-
# Arquivo: beeloo_wms_internal/wizard/beeloo_consolidation_wizard.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BeelooConsolidationWizard(models.TransientModel):
    _name = 'beeloo.consolidation.wizard'
    _description = 'Wizard de Consolidação de Sobras'

    # --- Ponto 1: Local de Retrabalho (Pode ser fixado via XML default ou aqui) ---
    location_id = fields.Many2one(
        'stock.location', 
        string='Local de Origem (Retrabalho)', 
        required=True
    )
    
    # Destino dos Paletes Vazios (RPM)
    rpm_dest_location_id = fields.Many2one(
        'stock.location',
        string='Destino dos Paletes Vazios',
        help="Local para onde os paletes de madeira sobressalentes serão enviados."
    )

    product_id = fields.Many2one(
        'product.product', 
        string='Produto', 
        required=True,
        #domain="[('type', '=', 'product')]"
    )

    # Trazemos o dado do cadastro para facilitar a conta visualmente
    palletization_qty = fields.Integer(
        string='Qtd por Palete',
        related='product_id.x_palletization_qty',
        readonly=True
    )

    line_ids = fields.One2many(
        'beeloo.consolidation.line', 
        'wizard_id', 
        string='Lotes Disponíveis'
    )

    # --- Totais Calculados ---
    total_qty_units = fields.Float(string='Total (Unidades)', compute='_compute_totals', store=True)
    total_qty_pallets = fields.Float(string='Total (Paletes)', compute='_compute_totals', store=True)
    
    # Previsão de sobra de madeira
    rpm_surplus_qty = fields.Integer(string='Sobras de Madeira (RPM)', compute='_compute_totals', help="Quantos paletes físicos vão sobrar vazios após a consolidação.")

    @api.depends('line_ids', 'line_ids.selected', 'palletization_qty')
    def _compute_totals(self):
        for record in self:
            selected_lines = record.line_ids.filtered(lambda l: l.selected)
            
            # 1. Total em Unidades
            total_u = sum(selected_lines.mapped('quantity'))
            record.total_qty_units = total_u

            # 2. Total em Paletes (Visual)
            if record.palletization_qty > 0:
                record.total_qty_pallets = total_u / record.palletization_qty
            else:
                record.total_qty_pallets = 0.0

            # 3. Lógica do RPM (Palete Vazio)
            # Se selecionamos 3 Lotes (3 paletes físicos parciais) e vamos gerar 1 Lote (1 palete físico)
            # Sobram: 3 - 1 = 2 paletes de madeira.
            input_pallets_count = len(selected_lines)
            
            # Aqui assumimos que a consolidação gera SEMPRE 1 novo palete (ou 1 novo lote)
            # Se a lógica for gerar mais de um, precisaremos ajustar.
            output_pallets_count = 1 if total_u > 0 else 0
            
            surplus = input_pallets_count - output_pallets_count
            record.rpm_surplus_qty = surplus if surplus > 0 else 0

    def action_search_lots(self):
        """ Busca Lotes no Local de Retrabalho """
        self.ensure_one()
        self.line_ids.unlink()
        
        domain = [
            ('location_id', '=', self.location_id.id),
            ('product_id', '=', self.product_id.id),
            ('quantity', '>', 0)
        ]
        # Busca quants agrupados seria ideal, mas vamos listar os quants diretos
        quants = self.env['stock.quant'].search(domain)
        
        lines = []
        for q in quants:
            lines.append((0, 0, {
                'lot_id': q.lot_id.id,
                'quantity': q.quantity,
                'uom_id': q.product_uom_id.id,
                'stock_quant_id': q.id,
                'selected': False, # Padrão desmarcado para forçar conferência
            }))
        
        self.write({'line_ids': lines})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_consolidate(self):
        """ 
        Executa a Consolidação com Fracionamento Inteligente (b6p-012):
        1. Consome todos os lotes selecionados (zera saldo antigo).
        2. Calcula quantos paletes cheios e qual a sobra.
        3. Gera múltiplos lotes novos (Ex: 3 Cheios + 1 Parcial).
        4. Calcula se sobrou madeira (RPM) e move.
        """
        self.ensure_one()
        
        # --- 1. Validações e Preparação ---
        selected_lines = self.line_ids.filtered(lambda l: l.selected)
        if not selected_lines:
            raise UserError(_("Selecione pelo menos um lote para consolidar."))

        # Validação do Local de Produção
        virtual_production_loc = self.env['stock.location'].search([
            ('usage', '=', 'production'),
            ('company_id', 'in', [self.env.company.id, False])
        ], limit=1)
        if not virtual_production_loc:
            raise UserError(_("Local de Produção Virtual não encontrado."))

        # --- 2. Consumo dos Lotes Antigos (Saída para Virtual) ---
        moves_to_process = []
        
        # Variáveis para controle da lógica
        total_qty_to_process = 0.0
        input_pallets_count = len(selected_lines) # Quantos paletes físicos entraram na operação
        
        for line in selected_lines:
            total_qty_to_process += line.quantity
            
            # Movimento de Saída (Consumo)
            move_out = self.env['stock.move'].create({
                'name': f'Consumo Repaletização: {line.lot_id.name}',
                'product_id': self.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.quantity,
                'location_id': self.location_id.id,
                'location_dest_id': virtual_production_loc.id,
                'state': 'draft',
            })
            move_out._action_confirm()
            move_out._do_unreserve() # Destrava reserva automática
            
            self.env['stock.move.line'].create({
                'move_id': move_out.id,
                'product_id': self.product_id.id,
                'product_uom_id': line.uom_id.id,
                'quantity': line.quantity, 
                'lot_id': line.lot_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': virtual_production_loc.id,
            })
            move_out.picked = True
            moves_to_process.append(move_out)

        # --- 3. Geração dos Novos Lotes (Entrada do Virtual) ---
        # Aqui está a lógica de Fracionamento (Loop)
        
        std_pallet_qty = self.product_id.x_palletization_qty
        remaining_qty = total_qty_to_process
        output_pallets_count = 0 # Contador de quantos paletes novos nasceram
        
        # Se não tiver paletização definida, gera um lote só com tudo
        if std_pallet_qty <= 0:
            std_pallet_qty = remaining_qty 

        while remaining_qty > 0:
            # Decide o tamanho do lote atual (Cheio ou Sobra)
            if remaining_qty >= std_pallet_qty:
                current_lot_qty = std_pallet_qty
            else:
                current_lot_qty = remaining_qty
            
            # Subtrai do saldo
            remaining_qty -= current_lot_qty
            output_pallets_count += 1
            
            # Cria nome do Lote Novo
            new_lot_name = self.env['ir.sequence'].next_by_code('beeloo.consolidation.lot') or \
                           f"REP-{fields.Datetime.now().strftime('%H%M%S')}-{output_pallets_count}"
            
            new_lot = self.env['stock.lot'].create({
                'name': new_lot_name,
                'product_id': self.product_id.id,
                'company_id': self.env.company.id,
            })

            # Cria Movimento de Entrada
            move_in = self.env['stock.move'].create({
                'name': f'Entrada Repaletização: {new_lot.name}',
                'product_id': self.product_id.id,
                'product_uom': self.product_id.uom_id.id,
                'product_uom_qty': current_lot_qty,
                'location_id': virtual_production_loc.id,
                'location_dest_id': self.location_id.id,
                'state': 'draft',
            })
            move_in._action_confirm()
            move_in._do_unreserve()
            
            self.env['stock.move.line'].create({
                'move_id': move_in.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'quantity': current_lot_qty,
                'lot_id': new_lot.id,
                'location_id': virtual_production_loc.id,
                'location_dest_id': self.location_id.id,
            })
            move_in.picked = True
            moves_to_process.append(move_in)

        # --- 4. Geração dos RPMs (Sobras de Madeira) ---
        # Lógica: Se entraram 5 paletes e saíram 3 novos, sobram 2 madeiras vazias.
        rpm_surplus = input_pallets_count - output_pallets_count
        
        if rpm_surplus > 0 and self.product_id.x_pallet_type_id:
            # Valida destino apenas se houver sobra real
            if not self.rpm_dest_location_id:
                 raise UserError(_(f"Esta operação vai gerar {rpm_surplus} paletes vazios. Informe o destino do RPM."))

            rpm_product = self.product_id.x_pallet_type_id
            
            move_rpm = self.env['stock.move'].create({
                'name': f'Sobra RPM (Input:{input_pallets_count} Output:{output_pallets_count})',
                'product_id': rpm_product.id,
                'product_uom': rpm_product.uom_id.id,
                'product_uom_qty': rpm_surplus, # Quantidade de Paletes Físicos
                'location_id': virtual_production_loc.id,
                'location_dest_id': self.rpm_dest_location_id.id,
                'state': 'draft',
            })
            move_rpm._action_confirm()
            move_rpm._do_unreserve()
            
            self.env['stock.move.line'].create({
                'move_id': move_rpm.id,
                'product_id': rpm_product.id,
                'product_uom_id': rpm_product.uom_id.id,
                'quantity': rpm_surplus,
                'location_id': virtual_production_loc.id,
                'location_dest_id': self.rpm_dest_location_id.id,
            })
            move_rpm.picked = True
            moves_to_process.append(move_rpm)

        # --- 5. Efetivação ---
        for move in moves_to_process:
            move.sudo()._action_done()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Repaletização Concluída'),
                'message': f'Entrada: {input_pallets_count} lotes. Saída: {output_pallets_count} novos lotes. RPM Liberado: {max(0, rpm_surplus)}.',
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }


class BeelooConsolidationLine(models.TransientModel):
    _name = 'beeloo.consolidation.line'
    _description = 'Linhas de Consolidação'

    wizard_id = fields.Many2one('beeloo.consolidation.wizard')
    selected = fields.Boolean(string="Selec.")
    lot_id = fields.Many2one('stock.lot', string="LPN / Lote")
    quantity = fields.Float(string="Qtd")
    uom_id = fields.Many2one('uom.uom', string="UdM")
    stock_quant_id = fields.Many2one('stock.quant')