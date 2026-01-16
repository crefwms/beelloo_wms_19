from odoo import models, fields, api
from odoo.exceptions import UserError

class BeelooScanner(models.TransientModel):
    _name = 'beeloo.scanner'
    _description = 'Console de Bipagem Dedicado'

    picking_id = fields.Many2one('stock.picking', required=True)
    barcode_input = fields.Char(string="Código de Barras")
    
    # Feedback visual
    last_message = fields.Char(string="Status", readonly=True)
    message_type = fields.Selection([('success', 'Sucesso'), ('error', 'Erro')], default='success')
    log_ids = fields.One2many('beeloo.scanner.log', 'scanner_id', string="Histórico")

    def process_barcode(self):
        """ Processa o código bipado e retorna a ação para manter o foco """
        self.ensure_one()
        barcode = (self.barcode_input or '').strip()
        
        if not barcode:
            return self._refresh_wizard()

        try:
            # Separa códigos se vierem colados (ex: leitor rápido)
            codes = [c.strip() for c in barcode.split('\n') if c.strip()]
            for code in codes:
                self._process_single_code(code)
            
        except Exception as e:
            self.message_type = 'error'
            self.last_message = f"❌ {str(e)}"
            self._log(f"Erro: {str(e)}")

        self.barcode_input = '' # Limpa campo
        return self._refresh_wizard()

    def _process_single_code(self, barcode):
        picking = self.picking_id
        
        # 1. Identificar o que foi bipado (Lote ou Produto)
        lot = self.env['stock.lot'].sudo().search([
            ('name', '=', barcode),
            ('product_id', 'in', picking.move_ids.product_id.ids)
        ], limit=1)

        product = False
        target_lot = False

        if lot:
            target_lot = lot
            product = lot.product_id
        else:
            # Tenta achar produto por EAN
            product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
            # Verifica se o produto pertence ao picking
            if product and product.id not in picking.move_ids.product_id.ids:
                product = False
        
        if not product:
            raise UserError(f"Código '{barcode}' não encontrado neste pedido.")

        # 2. Segurança de Serial Único
        if target_lot and product.tracking == 'serial':
            # Verifica se já existe linha FEITA com este serial
            duplicate = self.env['stock.move.line'].search([
                ('picking_id', '=', picking.id),
                ('lot_id', '=', target_lot.id),
                ('quantity', '>', 0)
            ], limit=1)
            if duplicate:
                self.message_type = 'error'
                self.last_message = f"⚠️ Serial {target_lot.name} já foi bipado!"
                return

        # 3. Tenta SWAP (Encontrar linha vazia para preencher)
        # Procura linha do mesmo produto, com Qty=0 e ainda não "Picked"
        candidate = self.env['stock.move.line'].search([
            ('picking_id', '=', picking.id),
            ('product_id', '=', product.id),
            ('quantity', '=', 0),
            ('picked', '=', False)
        ], limit=1, order='id asc') # Pega a primeira disponível

        if candidate:
            candidate.write({
                'lot_id': target_lot.id if target_lot else False,
                'quantity': 1.0,
                'picked': True
            })
            self.message_type = 'success'
            msg = f"✅ Confirmado: {target_lot.name if target_lot else product.name}"
            self.last_message = msg
            self._log(msg)
            return

        # 4. APPEND (Se não achou vaga, cria nova linha)
        # Busca o Movimento Pai para vincular
        move = picking.move_ids.filtered(lambda m: m.product_id == product)
        if not move:
             # Caso extremo onde move_ids não achou (ex: produto novo não previsto)
             # Criamos o move e a linha
             move = self.env['stock.move'].create({
                 'picking_id': picking.id,
                 'product_id': product.id,
                 'name': product.name,
                 'product_uom': product.uom_id.id,
                 'product_uom_qty': 0, # Extra
                 'location_id': picking.location_id.id,
                 'location_dest_id': picking.location_dest_id.id
             })

        self.env['stock.move.line'].create({
            'picking_id': picking.id,
            'move_id': move[0].id,
            'product_id': product.id,
            'lot_id': target_lot.id if target_lot else False,
            'quantity': 1.0,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picked': True
        })
        
        self.message_type = 'success'
        msg = f"➕ Adicionado Extra: {target_lot.name if target_lot else product.name}"
        self.last_message = msg
        self._log(msg)

    def _refresh_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'beeloo.scanner',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _log(self, msg):
        self.env['beeloo.scanner.log'].create({
            'scanner_id': self.id,
            'message': msg
        })

class BeelooScannerLog(models.TransientModel):
    _name = 'beeloo.scanner.log'
    _order = 'create_date desc'
    
    scanner_id = fields.Many2one('beeloo.scanner')
    message = fields.Char(string="Log")
    create_date = fields.Datetime(string="Hora")