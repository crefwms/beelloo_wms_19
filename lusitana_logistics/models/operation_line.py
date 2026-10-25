# -*- coding: utf-8 -*-
# models/operation_line.py

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)
RPM_CATEGORY_NAME = 'RPM'

class OperationLine(models.Model):
    _name = 'lusitana_logistics.operation_line'
    _description = 'Linha de Operação da Apresentação'
    _inherit = ['mail.thread']  # ← ADICIONA TRACKING

    # ---CAMPOS EXISTENTES ---
    presentation_id = fields.Many2one('lusitana_logistics.vehicle_presentation', string='Apresentação', required=True, ondelete='cascade')
    state = fields.Selection([('pendente', 'Pendente'), ('em_andamento', 'Em Andamento'), ('concluida', 'Concluída'), ('cancelada', 'Cancelada')], string='Status da Operação', default='pendente', required=True, readonly=True, copy=False)
    start_time = fields.Datetime(string='Início da Operação', readonly=True)
    end_time = fields.Datetime(string='Fim da Operação', readonly=True)
    duration = fields.Float(string='Duração (minutos)', compute='_compute_duration', store=True, readonly=True)
    operation_type_id = fields.Many2one('lusitana_logistics.operation_type', string='Tipo de Operação', required=True)
    direction = fields.Selection(related='operation_type_id.direction', readonly=True, store=True)
    dt_documento = fields.Char(string='DT (Doc. Transporte)')
    nf_referencia = fields.Char(string='NF de Referência')
    prioridade_carregamento_id = fields.Many2one('lusitana_logistics.priority', string='Prioridade')
    canal_vendas = fields.Selection(
        [
            ('y001', 'Y01 (Distribuidor)'), 
            ('y002', 'Y02 (Key Account)'), 
            ('y004', 'Y04 (Venda Direta)'),
            ('y006', 'Y06 (Intercompany)'),
            ('y055', 'Y055 (Exportação)'), 
            ('outros_canal', 'Outros')
        ], 
        string='Canal de Vendas'
    )
    cliente_id = fields.Many2one('res.partner', string='Cliente', domain="[('is_company', '=', True)]")
    tipo_carga = fields.Selection([('pa', 'PA (Produto Acabado)'), ('insumo', 'Insumo'), ('rpm', 'RPM (Ativos de Giro)'), ('outros_carga', 'Outros')], string='Tipo de Carga')
    origem_id = fields.Many2one('stock.location', string='Origem')
    destino_id = fields.Many2one('stock.location', string='Destino')
    agenda_line_ids = fields.One2many('lusitana_logistics.agenda_heineken_line_instance', 'operation_line_id', string='Produtos da Agenda')
    houve_troca_nf = fields.Boolean(string='Houve Troca de NF?')
    troca_nf_inicio = fields.Datetime(string='Início Troca NF')
    troca_nf_fim = fields.Datetime(string='Fim Troca NF')
    troca_nf_duracao = fields.Float(string='Duração Troca (min)', compute='_compute_troca_nf_duracao', store=True)

    urgency_level = fields.Selection(
        related='prioridade_carregamento_id.urgency_level',
        store=True,
        readonly=True
    )

    agenda_encontrada = fields.Boolean(
        string="Agenda Encontrada", 
        readonly=True, 
        default=False, 
        copy=False,
        help="Indica se uma agenda SAP foi encontrada e carregada para esta linha de operação."
    )
    
    # Campos de Conferência
    produto_em_conferencia_id = fields.Many2one('product.product', string='Produto em Conferência', help="Selecione o produto que você está bipando agora.")
    barcode_scan = fields.Char(string='Código de Barras', help="Bipe ou digite a etiqueta e pressione ENTER")
    conferencia_item_ids = fields.One2many('lusitana_logistics.conferencia_item', 'operation_line_id', string='Etiquetas Bipadas')
    
    # Campo computado para mostrar progresso em tempo real
    conferencia_progresso = fields.Char(string='Progresso', compute='_compute_conferencia_progresso', store=False)
    
    # ⚡ CAMPO DUMMY para forçar atualização da interface
    last_scan_timestamp = fields.Datetime(string='Última Bipagem', readonly=True, copy=False)

    # Produtos permitidos (baseado nas linhas da agenda)
    produto_ids_permitidos = fields.Many2many(
        'product.product',
        compute='_compute_produto_ids_permitidos',
        string='Produtos Permitidos',
        store=False
    )
    
    is_rpm_product_selected = fields.Boolean(
        string="É Produto RPM?",
        compute='_compute_is_rpm_product_selected',
        store=False # Não precisa salvar, é só para a UI
    )
    quantidade_manual_a_registrar = fields.Float(
        string="Qtd. Manual a Registrar",
        digits='Product Unit of Measure' # Usa a precisão padrão
    )
    
    @api.depends('produto_em_conferencia_id.categ_id')
    def _compute_is_rpm_product_selected(self):
        rpm_category = self.env['product.category'].search([('name', '=', RPM_CATEGORY_NAME)], limit=1)
        
        if not rpm_category:
            _logger.error(f"A Categoria de Produto com nome '{RPM_CATEGORY_NAME}' não foi encontrada!")
            for rec in self:
                rec.is_rpm_product_selected = False
            return
            
        for rec in self:
            rec.is_rpm_product_selected = bool(
                rec.produto_em_conferencia_id and 
                rec.produto_em_conferencia_id.categ_id == rpm_category
            )

    @api.depends('agenda_line_ids.product_id')
    def _compute_produto_ids_permitidos(self):
        """Retorna todos os produtos válidos da agenda."""
        for record in self:
            record.produto_ids_permitidos = record.agenda_line_ids.mapped('product_id')

    @api.depends('produto_em_conferencia_id', 'conferencia_item_ids', 'last_scan_timestamp','agenda_line_ids.quantidade_conferida_manual', 'is_rpm_product_selected')
    def _compute_conferencia_progresso(self):
        """Mostra o progresso da conferência (agora considera RPM)"""
        rpm_category = self.env['product.category'].search([('name', '=', RPM_CATEGORY_NAME)], limit=1)
        
        for record in self:
            if not record.produto_em_conferencia_id:
                record.conferencia_progresso = "➡️ Selecione um produto"
                continue
            
            product = record.produto_em_conferencia_id
            agenda_line = record.agenda_line_ids.filtered(lambda l: l.product_id == product)
            
            if not agenda_line:
                record.conferencia_progresso = "⚠️ Produto não está na agenda"
                continue

            # Pega a primeira linha (caso haja duplicidade, o que não deveria)
            agenda_line = agenda_line[0] 
            qtd_agendada = int(agenda_line.quantidade_paletes) # Sempre usamos paletes como alvo

            # Verifica se o produto selecionado é RPM
            is_rpm = record.is_rpm_product_selected # Usa o campo computado

            if is_rpm:
                # Para RPM, compara com a quantidade manual registrada
                qtd_conferida = int(agenda_line.quantidade_conferida_manual)
                label = "Registrado"
            else:
                # Para não-RPM, conta as bipagens
                qtd_conferida = self.env['lusitana_logistics.conferencia_item'].search_count([
                    ('operation_line_id', '=', record.id),
                    ('product_id', '=', product.id)
                ])
                label = "Bipadas"

            if qtd_conferida >= qtd_agendada:
                record.conferencia_progresso = f"✅ Completo! {qtd_conferida}/{qtd_agendada}"
            else:
                record.conferencia_progresso = f"📦 {label}: {qtd_conferida}/{qtd_agendada}"

    def action_registrar_quantidade_manual(self):
        self.ensure_one()

        if not self.is_rpm_product_selected:
             return { 'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Atenção!'), 'message': _("Este produto não é RPM. Use a bipagem normal."), 'type': 'warning', 'sticky': False}}
             
        if not self.produto_em_conferencia_id:
             return { 'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Atenção!'), 'message': _("Selecione um produto RPM antes de registrar a quantidade."), 'type': 'warning', 'sticky': False}}

        qty_manual = self.quantidade_manual_a_registrar
        if qty_manual <= 0:
             return { 'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Atenção!'), 'message': _("Informe uma quantidade manual maior que zero."), 'type': 'warning', 'sticky': False}}

        product = self.produto_em_conferencia_id
        agenda_line = self.agenda_line_ids.filtered(lambda l: l.product_id == product)
        if not agenda_line:
             # Isso não deveria acontecer se o produto foi selecionado, mas é uma segurança
             return { 'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Erro!'), 'message': _("Linha da agenda não encontrada para este produto."), 'type': 'danger', 'sticky': False}}

        agenda_line = agenda_line[0] # Pega a primeira
        qtd_agendada = int(agenda_line.quantidade_paletes)

        # Validação de Limite
        if qty_manual > qtd_agendada:
            return { 'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Quantidade Excedida!'), 'message': _("A quantidade informada (%s) excede a quantidade agendada (%s paletes).") % (int(qty_manual), qtd_agendada), 'type': 'danger', 'sticky': False}}
            
        # --- LÓGICA DE REGISTRO ---
        try:
            agenda_line.write({'quantidade_conferida_manual': qty_manual})
            _logger.info(f"✅ Quantidade manual registrada para {product.name} (AgendaLine: {agenda_line.id}): {qty_manual}")
            
            # Limpa o campo de entrada
            self.quantidade_manual_a_registrar = 0.0 
            
            # Retorna ação para recarregar a view (como fizemos para a bipagem)
            view_id = self.env.context.get('view_id', False)
            if not view_id:
                 view_id = self.env.ref('lusitana_logistics.view_operation_line_form').id 
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'res_id': self.id,
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'target': 'current',
                'context': {
                    **self.env.context,
                    'ODOO_NOTIFY': {
                        'type': 'success',
                        'message': _("Quantidade %s registrada para %s!") % (int(qty_manual), product.display_name),
                        'sticky': False,
                    }
                }
            }

        except Exception as e:
            _logger.error(f"Erro ao registrar quantidade manual: {e}")
            return { 'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': _('Erro no Servidor!'), 'message': _("Não foi possível registrar a quantidade: %s") % e, 'type': 'danger', 'sticky': True}}

    
    @api.onchange('barcode_scan')
    def _onchange_barcode_scan(self):
        """
        AUTO-SUBMIT: Quando o campo barcode_scan é preenchido (via scanner ou digitação + ENTER),
        este onchange dispara automaticamente a adição da etiqueta.
        """
        if self.barcode_scan and self.barcode_scan.strip():
            # Chama o método de adição automaticamente
            return self.action_adicionar_etiqueta()

    def action_adicionar_etiqueta(self):
        """
        Adiciona uma etiqueta bipada à conferência.
        SOLUÇÃO DEFINITIVA: Usa write() para forçar atualização da view.
        """
        self.ensure_one()

        # --- Validações iniciais ---
        if not self.barcode_scan or not self.barcode_scan.strip():
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Atenção!'),
                    'message': _("⚠️ Digite ou bipe uma etiqueta antes de adicionar!"),
                    'type': 'warning',
                    'sticky': False
                }
            }

        barcode_input = self.barcode_scan.strip()

        if not self.id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Atenção!'),
                    'message': _("⚠️ Salve a operação antes de iniciar a conferência!"),
                    'type': 'warning',
                    'sticky': False
                }
            }

        if not self.produto_em_conferencia_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Atenção!'),
                    'message': _("⚠️ Selecione um produto em 'Produto em Conferência'!"),
                    'type': 'warning',
                    'sticky': False
                }
            }

        product = self.produto_em_conferencia_id
        agenda_line = self.agenda_line_ids.filtered(lambda l: l.product_id == product)

        if not agenda_line:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro!'),
                    'message': _("❌ O produto '%s' não está na lista de produtos agendados!") % product.display_name,
                    'type': 'danger',
                    'sticky': False
                }
            }

        # --- Validação de Limite (SEMPRE busca do banco) ---
        qtd_conferida = self.env['lusitana_logistics.conferencia_item'].search_count([
            ('operation_line_id', '=', self.id),
            ('product_id', '=', product.id)
        ])
        qtd_agendada = int(sum(agenda_line.mapped('quantidade_paletes')))

        if qtd_conferida >= qtd_agendada:
            # ⚡ USA WRITE para limpar (força atualização da view)
            self.write({'barcode_scan': False})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Limite Atingido!'),
                    'message': _("⚠️ Limite atingido para '%s'!\nConferido: %s/%s Paletes") % 
                               (product.display_name, qtd_conferida, qtd_agendada),
                    'type': 'warning',
                    'sticky': False
                }
            }

        # --- Validação de Duplicidade ---
        duplicado = self.env['lusitana_logistics.conferencia_item'].search([
            ('operation_line_id', '=', self.id),
            ('barcode', '=', barcode_input)
        ], limit=1)

        if duplicado:
            # ⚡ USA WRITE para limpar
            self.write({'barcode_scan': False})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Duplicado!'),
                    'message': _("❌ Etiqueta '%s' já foi bipada!") % barcode_input,
                    'type': 'danger',
                    'sticky': False
                }
            }

        # --- Criação do Item ---
        try:
            # Cria o registro no banco
            new_item = self.env['lusitana_logistics.conferencia_item'].create({
                'operation_line_id': self.id,
                'product_id': product.id,
                'barcode': barcode_input
            })

            _logger.info(f"✅ Etiqueta criada: ID={new_item.id}, Barcode={barcode_input}, Operation={self.id}")

            # Recalcula para mostrar na mensagem
            qtd_conferida_atualizada = qtd_conferida + 1

            # ⚡ SOLUÇÃO DEFINITIVA: Usa WRITE para forçar atualização da view
            # Atualiza o timestamp dummy + limpa o barcode em UMA ÚNICA operação write()
            self.write({
                'barcode_scan': False,
                'last_scan_timestamp': fields.Datetime.now()  # ← Força trigger de atualização
            })

            # ⚡ Retorna notificação simples (sem reload)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '✅ Etiqueta Adicionada!',
                    'message': f'{product.display_name}\nEtiqueta: {barcode_input}\nProgresso: {qtd_conferida_atualizada}/{qtd_agendada}',
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"❌ Erro ao criar item de conferência: {e}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Erro no Servidor!'),
                    'message': _("Não foi possível salvar a etiqueta: %s") % str(e),
                    'type': 'danger',
                    'sticky': True
                }
            }

    @api.depends('troca_nf_inicio', 'troca_nf_fim')
    def _compute_troca_nf_duracao(self):
        """Calcula a duração da troca de NF em minutos"""
        for line in self:
            if line.troca_nf_inicio and line.troca_nf_fim:
                delta = line.troca_nf_fim - line.troca_nf_inicio
                line.troca_nf_duracao = delta.total_seconds() / 60.0
            else:
                line.troca_nf_duracao = 0.0

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        """Calcula a duração da operação em minutos"""
        for line in self:
            if line.start_time and line.end_time:
                line.duration = (line.end_time - line.start_time).total_seconds() / 60.0
            else:
                line.duration = 0.0

    def action_start(self):
        """Inicia a operação"""
        self.ensure_one()
        if self.presentation_id.state not in ['entrada', 'em_operacao']:
            raise ValidationError(
                "A operação não pode ser iniciada! A Apresentação precisa estar no status 'Entrada no Pátio' ou 'Em Operação'."
            )
        if self.state != 'pendente':
            raise ValidationError("Esta operação não está 'Pendente' e não pode ser iniciada.")
        
        self.write({
            'state': 'em_andamento', 
            'start_time': datetime.now()
        })
        self.presentation_id._update_presentation_state()

    def action_finish(self):
        """Finaliza a operação com validação (agora considera RPM)"""
        self.ensure_one()
        _logger.info(f"--- INICIANDO VALIDAÇÃO FINAL PARA OPERAÇÃO {self.id} ---")
        
        if self.state != 'em_andamento':
            raise ValidationError(_("Esta operação não está em andamento e não pode ser finalizada."))

        rpm_category = self.env['product.category'].search([('name', '=', RPM_CATEGORY_NAME)], limit=1)

        # Validação: Quantidade vs. Agendada
        if self.agenda_line_ids:
            for agendado in self.agenda_line_ids:
                qtd_agendada = int(agendado.quantidade_paletes)
                
                # Verifica se é RPM
                is_rpm = bool(rpm_category and agendado.product_id.categ_id == rpm_category)

                if is_rpm:
                    # Para RPM, usa a quantidade manual
                    qtd_conferida = int(agendado.quantidade_conferida_manual)
                    tipo = "Manual"
                else:
                    # Para não-RPM, conta as bipagens
                    qtd_conferida = self.env['lusitana_logistics.conferencia_item'].search_count([
                        ('operation_line_id', '=', self.id),
                        ('product_id', '=', agendado.product_id.id)
                    ])
                    tipo = "Bipada"
                
                _logger.info(
                    f"Validação Final - Produto '{agendado.product_id.display_name}' (RPM: {is_rpm}): "
                    f"Agendado={qtd_agendada} PLT, Conferido ({tipo})={qtd_conferida}"
                )

                # Validações (menor ou maior)
                if qtd_conferida < qtd_agendada:
                    raise ValidationError(
                        _("❌ Conferência incompleta!\n\nProduto: %s\nConferido (%s): %s\nAgendado: %s Paletes") % 
                        (agendado.product_id.display_name, tipo, qtd_conferida, qtd_agendada)
                    )
                if qtd_conferida > qtd_agendada:
                    raise ValidationError(
                        _("❌ Quantidade excedida!\n\nProduto: %s\nConferido (%s): %s\nAgendado: %s Paletes") % 
                        (agendado.product_id.display_name, tipo, qtd_conferida, qtd_agendada)
                    )

        # Finaliza a operação (igual a antes)
        self.write({'state': 'concluida', 'end_time': datetime.now()})
        self.presentation_id._update_presentation_state()
        _logger.info(f"✅ VALIDAÇÃO FINAL CONCLUÍDA COM SUCESSO")
        return { # Retorna notificação de sucesso
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': { 'title': '✅ Operação Finalizada!', 'message': 'A conferência foi concluída com sucesso.', 'type': 'success', 'sticky': False}
        }

    def action_reset(self):
        """Reseta a operação para o estado pendente"""
        self.ensure_one()
        if self.state not in ['em_andamento', 'concluida']:
            raise ValidationError("Apenas operações em andamento ou concluídas podem ser resetadas.")
        
        self.write({
            'state': 'pendente', 
            'start_time': False, 
            'end_time': False
        })
        self.presentation_id._update_presentation_state()

    @api.onchange('dt_documento', 'direction')
    def _onchange_dt_documento(self):
        
        # --- 1. Lógica de Limpeza ---
        if not self.dt_documento:
            _logger.info("_onchange_dt_documento: DT limpo, limpando campos relacionados.")
            self.canal_vendas = False
            self.cliente_id = False
            self.prioridade_carregamento_id = False
            self.agenda_line_ids = [(5, 0, 0)]
            return

        dt = self.dt_documento.strip()
        _logger.info(f"_onchange_dt_documento: Iniciando busca/verificação para DT: '{dt}'")

        # Limpa campos ANTES de buscar/validar
        self.canal_vendas = False
        self.cliente_id = False
        self.prioridade_carregamento_id = False
        self.agenda_line_ids = [(5, 0, 0)]

        # --- 3. Verificação de Duplicidade (LÓGICA REATIVADA E CORRIGIDA) ---
        _logger.info(f"Verificando duplicidade para DT: {dt}")

        # Pega o ID salvo da apresentação (None se for uma apresentação nova)
        current_presentation_id = self.presentation_id._origin.id
        # Pega o ID salvo da linha atual (None se for uma linha nova)
        current_line_id = self._origin.id

        duplication_domain = [
            ('dt_documento', '=', dt),
            ('state', '!=', 'cancelada')
        ]

        if current_presentation_id:
            # Se a apresentação já existe, só procura nela
            duplication_domain.append(('presentation_id', '=', current_presentation_id))
        else:
            # Se a apresentação é nova, só procura em linhas órfãs (sem apresentação)
            duplication_domain.append(('presentation_id', '=', False))

        if current_line_id:
            # Exclui a si mesmo da busca (caso esteja editando uma linha já salva)
            duplication_domain.append(('id', '!=', current_line_id))
            
        operacoes_existentes = self.env['lusitana_logistics.operation_line'].search(duplication_domain)
        
        if operacoes_existentes:
            _logger.warning(f"DT {dt} já está em uso nesta apresentação.")
            return {
                'warning': {
                    'title': _("DT Duplicado!"),
                    'message': _("Este DT (%s) já está sendo usado em outra linha desta mesma Apresentação.") % dt
                }
            }
        # --- FIM DA VERIFICAÇÃO DE DUPLICIDADE ---

        # --- 4. Lógica de Busca (Sabemos que está funcionando) ---
        _logger.info(f"DT '{dt}' está livre. Carregando agenda...")
        self._carregar_agenda_do_dt()
        
        if not self.agenda_line_ids:
            _logger.warning(f"DT '{dt}' não encontrado na agenda.")
            return {
                'warning': {
                    'title': _("DT Não Agendado!"),
                    'message': _("Este DT (%s) não foi encontrado na Agenda. Verifique o cadastro da Agenda ou o DT digitado.") % dt
                }
            }
            
        #_logger.info(f"DT '{dt}' está livre. Buscando na agenda...")
        #agenda = self.env['lusitana_logistics.agenda_heineken'].search([('dt_documento', '=', dt)], limit=1)

        #if agenda:
        #    _logger.info(f"Agenda encontrada para DT '{dt}'. Preenchendo dados...")
        #    # Preenche os dados
        #    self.canal_vendas = agenda.canal_vendas
        #    self.prioridade_carregamento_id = agenda.prioridade_id.id
        #    partner = self.env['res.partner']
        #    if agenda.cliente_code:
        #        partner = self.env['res.partner'].search([('ref', '=', agenda.cliente_code.strip())], limit=1)
        #    if not partner and agenda.cliente_name:
        #        partner = self.env['res.partner'].search([('name', 'ilike', agenda.cliente_name.strip())], limit=1)
        #    self.cliente_id = partner.id if partner else False
        #    
        #    linhas_para_criar = []
        #    for linha_agenda in agenda.line_ids:
        #        linhas_para_criar.append((0, 0, {
        #            'product_id': linha_agenda.product_id.id,
        #            'quantidade': linha_agenda.quantidade,
        #            'quantidade_paletes': linha_agenda.quantidade_paletes
        #        }))
        #    self.agenda_line_ids = linhas_para_criar
        #    _logger.info(f"Dados preenchidos para DT '{dt}'.")
        #else:
        #    _logger.warning(f"DT '{dt}' não encontrado na agenda.")
        #    return {
        #        'warning': {
        #            'title': _("DT Não Agendado!"),
        #            'message': _("Este DT (%s) não foi encontrado na Agenda. Verifique o cadastro da Agenda ou o DT digitado.") % dt
        #        }
        #    }
    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescreve o create para garantir que as linhas da agenda sejam salvas corretamente
        """
        records = super(OperationLine, self).create(vals_list)
        
        for record in records:
            # Se tem DT mas não tem linhas, busca novamente
            if record.dt_documento and not record.agenda_line_ids:
                _logger.info(f"CREATE: DT {record.dt_documento} sem linhas. Recarregando agenda...")
                record._carregar_agenda_do_dt()
        
        return records

    def write(self, vals):
        """
        Sobrescreve o write para garantir persistência das linhas
        """
        res = super(OperationLine, self).write(vals)
        
        # Se o DT foi alterado, recarrega a agenda
        if 'dt_documento' in vals:
            for record in self:
                if record.dt_documento and not record.agenda_line_ids:
                    _logger.info(f"WRITE: DT {record.dt_documento} sem linhas. Recarregando agenda...")
                    record._carregar_agenda_do_dt()
        
        return res

    def _carregar_agenda_do_dt(self):
        """
        Método auxiliar para carregar dados da agenda (evita duplicação de código)
        """
        self.ensure_one()
        
        if not self.dt_documento:
            return
        
        dt = self.dt_documento.strip()
        agenda = self.env['lusitana_logistics.agenda_heineken'].search([('dt_documento', '=', dt)], limit=1)
        
        if not agenda:
            _logger.warning(f"Agenda não encontrada para DT: {dt}")
            return
        
        _logger.info(f"Carregando agenda para DT: {dt}")
        
        # Limpa linhas existentes
        self.agenda_line_ids = [(5, 0, 0)]
        
        # Carrega dados da agenda
        self.canal_vendas = agenda.canal_vendas
        self.prioridade_carregamento_id = agenda.prioridade_id.id
        self.agenda_encontrada = True
        
        # Busca cliente
        partner = False
        if agenda.cliente_code:
            partner = self.env['res.partner'].search([('ref', '=', agenda.cliente_code.strip())], limit=1)
        if not partner and agenda.cliente_name:
            partner = self.env['res.partner'].search([('name', 'ilike', agenda.cliente_name.strip())], limit=1)
        self.cliente_id = partner.id if partner else False
        
        # Cria as linhas da agenda
        linhas_para_criar = []
        for linha_agenda in agenda.line_ids:
            linhas_para_criar.append((0, 0, {
                'product_id': linha_agenda.product_id.id,
                'quantidade': linha_agenda.quantidade,
                'quantidade_paletes': linha_agenda.quantidade_paletes
            }))
        
        self.agenda_line_ids = linhas_para_criar
        _logger.info(f"✅ {len(linhas_para_criar)} linhas carregadas para DT {dt}")