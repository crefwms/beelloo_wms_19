from odoo import models, fields, api

class BeelooOutboundReport(models.TransientModel):
    _name = 'beeloo.outbound.report'
    _description = 'Gerador de Dados para NFe (Explosão + Lastro)'

    picking_id = fields.Many2one('stock.picking', required=True)
    report_text = fields.Text(string="Dados para NFe (Ctrl+C)", readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(BeelooOutboundReport, self).default_get(fields)
        if self.env.context.get('active_id'):
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            res['picking_id'] = picking.id
            res['report_text'] = self._compute_traceability_text(picking)
        return res

    def _compute_traceability_text(self, picking):
        lines = []
        
        # --- 1. BUSCA A AGENDA E DT (Conexão Reversa) ---
        # Procura qual agenda tem este picking como filho
        agenda = self.env['beeloo.agenda'].search([
            ('stock_picking_id', '=', picking.id)
        ], limit=1)

        dt_valor = agenda.dt_documento if agenda else "N/A"
        agenda_id = agenda.id if agenda else "N/A"
        
        # --- 2. CABEÇALHO ---
        lines.append(f"=== DADOS PARA EMISSÃO DE NOTA FISCAL ===")
        lines.append(f"Remessa: {picking.name}")
        lines.append(f"DT: {dt_valor} (Agenda ID: {agenda_id})")
        lines.append(f"Destino: {picking.partner_id.name or 'N/A'}")
        lines.append("-" * 40)

        # --- 3. EXPLOSÃO E RASTREABILIDADE ---
        for move_line in picking.move_line_ids:
            if move_line.quantity == 0: continue

            product = move_line.product_id
            qty_moved = move_line.quantity
            lot = move_line.lot_id
            
            # O "EXPLODIDOR" VIRTUAL
            bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', product.product_tmpl_id.id)
            ], limit=1)

            final_components = []
            
            if bom:
                lines.append(f"[INFO] Convertendo {qty_moved}x {product.name}...")
                for bom_line in bom.bom_line_ids:
                    comp_qty = bom_line.product_qty * qty_moved
                    final_components.append({
                        'product': bom_line.product_id,
                        'qty': comp_qty,
                        'lot': lot # Mantém o lote do palete
                    })
            else:
                final_components.append({
                    'product': product,
                    'qty': qty_moved,
                    'lot': lot
                })

            # LOOP DOS ITENS FINAIS (CERVEJAS)
            for item in final_components:
                p_name = item['product'].name
                p_qty = item['qty']
                p_lot = item['lot']
                
                origin_nf = "N/A"
                origin_date = "N/A"
                origin_dt = "N/A"

                if p_lot:
                    # RASTREABILIDADE: Busca a Entrada Original desse Lote
                    origin_move = self.env['stock.move.line'].search([
                        ('lot_id', '=', p_lot.id),
                        ('picking_id.picking_type_code', '=', 'incoming'),
                        ('state', '=', 'done')
                    ], limit=1, order='date desc')
                    
                    if origin_move:
                        origin_picking = origin_move.picking_id
                        
                        # Pega NF de Entrada (Campo customizado do Inbound)
                        origin_nf = getattr(origin_picking, 'x_nfe_number', False) or "S/NF"
                        origin_date = origin_picking.date_done.strftime('%d/%m/%Y') if origin_picking.date_done else "N/D"
                        
                        # Pega DT de Entrada (Busca Reversa na Agenda da Entrada)
                        origin_agenda = self.env['beeloo.agenda'].search([
                            ('stock_picking_id', '=', origin_picking.id)
                        ], limit=1)
                        origin_dt = origin_agenda.dt_documento if origin_agenda else "N/A"

                # MONTA A LINHA DE TEXTO
                lines.append(f"ITEM: {p_name}")
                lines.append(f"QTD: {p_qty} | LOTE: {p_lot.name if p_lot else 'S/L'}")
                lines.append(f"ORIGEM: NF {origin_nf} ({origin_date}) | DT ENT: {origin_dt}")
                lines.append(f"----------------------------------------")

        return "\n".join(lines)