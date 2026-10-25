# -*- coding: utf-8 -*-
# wizards/agenda_import_wizard.py

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import csv
import io
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class AgendaImportWizard(models.TransientModel):
    _name = 'lusitana_logistics.agenda_import_wizard'
    _description = 'Assistente para Importação de Agenda SAP'

    file_upload = fields.Binary(string='Arquivo da Agenda (.csv)', required=True)
    file_name = fields.Char(string='Nome do Arquivo')
    delimiter = fields.Selection([(',', 'Vírgula (,)'), (';', 'Ponto e Vírgula (;)')], 
                                  string='Separador', default=';', required=True)

    def action_import_file(self):
        self.ensure_one()
        if not self.file_upload:
            raise UserError(_("Por favor, selecione um arquivo para importar."))

        try:
            decoded_file = base64.b64decode(self.file_upload).decode('latin-1')
            file_input = io.StringIO(decoded_file)
            reader = csv.reader(file_input, delimiter=self.delimiter)
        except Exception as e:
            raise UserError(_("Não foi possível ler o arquivo. Verifique se é um CSV válido (formato latin-1). Erro: %s") % e)

        try:
            next(reader) # Pula o cabeçalho
        except StopIteration:
            raise UserError(_("O arquivo está vazio ou o cabeçalho não foi encontrado."))

        agenda_model = self.env['lusitana_logistics.agenda_heineken']
        agenda_line_model = self.env['lusitana_logistics.agenda_heineken_line']
        product_model = self.env['product.product']
        priority_model = self.env['lusitana_logistics.priority']
        partner_model = self.env['res.partner']
        
        created_count = 0
        updated_count = 0
        agendas_processadas = {}
        
        MAP_CANAL = {
            'Y001': 'y001', 'Y002': 'y002', 'Y004': 'y004',
            'Y006': 'y006', 'Y055': 'y055',
        }

        priority_cache = {}
        partner_cache = {}

        for i, row in enumerate(reader):
            if len(row) < 13:
                _logger.warning(f"Pulando linha {i+2}: número de colunas insuficiente ({len(row)}).")
                continue

            dt_documento = row[0].strip()
            if not dt_documento:
                _logger.warning(f"Pulando linha {i+2}: DT (Doc. Transporte) está vazio.")
                continue

            try:
                hora_agendamento = row[1].strip()
                
                canal_csv = row[2].strip().upper()
                canal_key = MAP_CANAL.get(canal_csv, 'outros_canal')
                
                cliente_code = row[3].strip()
                
                prioridade_txt = row[4].strip().upper()
                prioridade_id = False
                if prioridade_txt:
                    if prioridade_txt in priority_cache:
                        prioridade_id = priority_cache[prioridade_txt]
                    else:
                        # (REQ 3) Isto está correto, busca pelo CÓDIGO SAP
                        priority_obj = priority_model.search([('sap_code', '=', prioridade_txt)], limit=1)
                        if priority_obj:
                            prioridade_id = priority_obj.id
                            priority_cache[prioridade_txt] = priority_id
                        else:
                            raise UserError(_("A Prioridade '%s' (DT: %s, Linha: %s) não foi encontrada no cadastro de Prioridades (Campo 'Código SAP').") 
                                            % (prioridade_txt, dt_documento, i+2))
                
                cliente_name = row[5].strip()
                produto_sku = row[6].strip().lstrip('0')
                product_descr_sap = row[7].strip()
                
                qty_str = row[8].strip().replace('.', '').replace(',', '.')
                quantidade = float(qty_str)
                
                plt_str = row[9].strip().replace('.', '').replace(',', '.')
                paletes = float(plt_str) if plt_str else 0.0
                
                deposito = row[10].strip()
                
                transportadora_nome_csv = row[11].strip()
                transportadora_id = False
                if transportadora_nome_csv:
                    if transportadora_nome_csv in partner_cache:
                        transportadora_id = partner_cache[transportadora_nome_csv]
                    else:
                        transportadora_obj = partner_model.search([('name', 'ilike', transportadora_nome_csv)], limit=1)
                        if transportadora_obj:
                            transportadora_id = transportadora_obj.id
                            partner_cache[transportadora_nome_csv] = transportadora_id
                        else:
                            _logger.warning(f"Transportadora '{transportadora_nome_csv}' (DT: {dt_documento}) não encontrada no Odoo. O campo ficará vazio.")
                            partner_cache[transportadora_nome_csv] = False

                data_agendamento = datetime.strptime(row[12].strip(), '%d/%m/%Y').date()

                if not produto_sku:
                     _logger.warning(f"Pulando linha {i+2} (DT: {dt_documento}): SKU do produto está vazio.")
                     continue

                product = product_model.search([('default_code', '=', produto_sku)], limit=1)
                if not product:
                    raise UserError(_("O produto com SKU '%s' (DT: %s, Linha: %s) não foi encontrado no cadastro de produtos (Campo 'Referência Interna').") 
                                    % (produto_sku, dt_documento, i+2))

                if dt_documento not in agendas_processadas:
                    agenda = agenda_model.search([('dt_documento', '=', dt_documento)], limit=1)
                    
                    agenda_vals = {
                        'transportadora_id': transportadora_id,
                        'direction': 'outbound', # (REQ 2) Hardcoded, pois a agenda SAP é outbound
                        'centro': deposito, 
                        'deposito': deposito,
                        'canal_vendas': canal_key,
                        'prioridade_id': prioridade_id,
                        'cliente_code': cliente_code,
                        'cliente_name': cliente_name,
                        'data_agendamento': data_agendamento,
                        'hora_agendamento': hora_agendamento,
                    }
                    
                    if agenda:
                        agenda.line_ids.unlink()
                        agenda.write(agenda_vals)
                        updated_count += 1
                    else:
                        agenda_vals['dt_documento'] = dt_documento
                        agenda = agenda_model.create(agenda_vals)
                        created_count += 1
                    agendas_processadas[dt_documento] = agenda
                else:
                    agenda = agendas_processadas[dt_documento]
                
                agenda_line_model.create({
                    'agenda_id': agenda.id,
                    'product_id': product.id,
                    'product_descr_sap': product_descr_sap,
                    'quantidade': quantidade,
                    'quantidade_paletes': paletes,
                })
            
            except (ValueError, IndexError, Exception) as e:
                if isinstance(e, UserError):
                    raise e
                _logger.error(f"Erro ao processar linha {i+2} para o DT {dt_documento}: {e}")
                raise UserError(_("Erro ao processar a linha %s (DT: %s). Verifique o formato das colunas (data, qtd, sku). Erro: %s") % (i+2, dt_documento, e))

        return {
            'type': 'ir.actions.client', 'tag': 'display_notification',
            'params': { 'title': _('Importação Concluída'), 'message': _('%s agendamentos criados e %s atualizados.') % (created_count, updated_count), 'type': 'success', 'sticky': True }
        }