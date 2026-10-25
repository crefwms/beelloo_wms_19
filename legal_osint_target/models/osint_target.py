# -*- coding: utf-8 -*-
import logging
import time
import random
import re
from urllib.parse import unquote
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class OsintTarget(models.Model):
    _name = 'osint.target'
    _description = 'Alvo de Monitoramento Jurídico'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Nome do Alvo/Processo', required=True, tracking=True)
    identifier = fields.Char(string='CPF/CNPJ ou Nº Processo', tracking=True)
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('active', 'Monitorando'),
        ('paused', 'Pausado')
    ], default='draft', string='Status', tracking=True)
    
    last_check = fields.Datetime(string='Última Verificação', readonly=True)
    next_check = fields.Datetime(string='Próxima Verificação')
    
    result_ids = fields.One2many('osint.result', 'target_id', string='Resultados Encontrados')
    
    # Integrações Enterprise
    project_id = fields.Many2one('project.project', string='Projeto / OS', tracking=True)
    task_id = fields.Many2one('project.task', string='Tarefa Vinculada', tracking=True)
    google_drive_folder_id = fields.Char(string='ID da Pasta (G Drive)', tracking=True)
    whatsapp_group_id = fields.Char(string='ID do Grupo/WhatsApp', tracking=True)
    company_id = fields.Many2one('res.company', string='Empresa', default=lambda self: self.env.company, required=True, tracking=True)

    def _get_rotated_headers(self):
        """
        Retorna headers de diferentes navegadores para rotar em cada tentativa.
        """
        profiles = [
            # Chrome Windows 11
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9',
                'Referer': 'https://www.google.com.br/',
            },
            # Safari MacOS
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9',
                'Referer': 'https://duckduckgo.com/',
            },
            # Firefox Linux
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
                'Referer': 'https://www.bing.com/',
            }
        ]
        headers = random.choice(profiles)
        headers.update({
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
        })
        return headers

    def action_check_now(self):
        """
        Plano de Resiliência 3.0 com Deep Search e Integração Enterprise.
        """
        import requests
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            BeautifulSoup = None

        _logger.info("### OSINT: Iniciando Plano 3.0 + Deep Search para %s registros", len(self))
        session = requests.Session()

        for record in self:
            # LIMPEZA DE CACHE/COOKIES
            session.cookies.clear()
            
            time.sleep(random.uniform(2, 4))
            query = record.identifier or record.name
            
            # --- TENTATIVA 1: ESCAVADOR (Alvo Principal) ---
            _logger.info("### OSINT: Tentativa no Escavador para %s", query)
            success = False
            content_html = ""
            found_urls = []
            source = ""
            current_headers = self._get_rotated_headers()
            
            try:
                resp = session.get(f"https://www.escavador.com/busca?q={query}", headers=current_headers, timeout=12)
                if resp.status_code == 200:
                    success = True
                    source = "Escavador"
                    content_html, found_urls = self._extract_relevant_data(resp.text, query, BeautifulSoup)
            except Exception:
                pass

            # --- TENTATIVA 2: DUCKDUCKGO (Fallback se Escavador falhou ou 403) ---
            if not success:
                _logger.info("### OSINT: Escavador bloqueou ou falhou. Tentando DuckDuckGo para %s", query)
                try:
                    ddg_url = f"https://html.duckduckgo.com/html/?q=processo+judicial+{query}"
                    resp = session.get(ddg_url, headers=self._get_rotated_headers(), timeout=12)
                    if resp.status_code == 200:
                        success = True
                        source = "DuckDuckGo (Fallback)"
                        content_html, found_urls = self._extract_relevant_data(resp.text, query, BeautifulSoup)
                except Exception:
                    pass

            # --- ETAPA DE DEEP SEARCH (Mergulho Profundo) ---
            process_number = False
            if success and found_urls:
                first_legal_url = found_urls[0]
                _logger.info("### OSINT: Deep Search ativado para URL: %s", first_legal_url)
                record.message_post(body=f"🔍 <b>Deep Search:</b> Analisando conteúdo interno de {first_legal_url}...")
                
                deep_content, deep_process = self._deep_search_and_extract(session, first_legal_url, self._get_rotated_headers(), BeautifulSoup)
                if deep_process:
                    process_number = deep_process
                    content_html += f"<div style='border: 1px solid #17a2b8; padding: 10px; margin-top: 10px; background: #e3f2fd;'><b>🎯 Processo Encontrado via Deep Search:</b> {process_number}<br/>{deep_content}</div>"

            # --- TENTATIVA 3: FALHA TOTAL ---
            if not success:
                _logger.warning("### OSINT: Todos os alvos reais bloquearam %s.", query)
                record.message_post(body="❌ <b>Falha Total:</b> Todos os buscadores (Escavador/DuckDuckGo) bloquearam a conexão (403/400).")
                continue

            # Gravando o Resultado
            result = self.env['osint.result'].create({
                'target_id': record.id,
                'name': f"{source}: {fields.Datetime.now().strftime('%d/%m %H:%M')}",
                'content': content_html,
                'process_number': process_number,
                'date': fields.Datetime.now(),
                'summary': f"Processo: {process_number}" if process_number else f"Monitoramento via {source}",
            })
            
            msg = f"✅ Verificação via <b>{source}</b> concluída para o alvo {record.name}."
            record.message_post(body=msg)
            
            # --- INTEGRAÇÃO ENTERPRISE: Notificar Tarefa Vinculada ---
            if record.task_id:
                notif_body = f"🚀 <b>OSINT Atualizado:</b> Identificado novo andamento para o alvo <b>{record.name}</b>.<br/> {result.summary}<br/> <a href='/web#id={result.id}&model=osint.result&view_type=form'>Ver Detalhes</a>"
                record.task_id.message_post(body=notif_body)
                _logger.info("### OSINT: Notificação enviada para Tarefa %s", record.task_id.id)

            # --- INTEGRAÇÃO ENTERPRISE: WhatsApp & G-Drive (Placeholders) ---
            if record.whatsapp_group_id:
                record._post_to_whatsapp(f"Atualização OSINT para {record.name}: {result.summary}")
            
            record.last_check = fields.Datetime.now()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Enterprise Sync Concluído',
                'message': 'O robô jurídico sincronizou os dados com Tarefas e Integrações.',
                'sticky': False,
                'type': 'success',
            }
        }

    def _post_to_whatsapp(self, message):
        """ Placeholder para integração via Evolution/Z-API """
        _logger.info("### OSINT WHATSAPP (Stub): %s", message)
        return True

    def _upload_to_drive(self, file_content):
        """ Placeholder para integração com Google Drive API """
        _logger.info("### OSINT DRIVE (Stub): Upload de arquivo iniciado...")
        return True

    def _deep_search_and_extract(self, session, url, headers, bs_lib):
        """
        Acessa um link específico e tenta extrair o número do processo (CNJ).
        """
        try:
            # Limpeza de URL (Decodificação de caracteres especiais)
            clean_url = unquote(url)
            _logger.info("### OSINT: Acessando URL Limpa: %s", clean_url)
            
            time.sleep(random.uniform(1, 2))
            resp = session.get(clean_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                text_content = resp.text
                process_num = self._extract_process_numbers(text_content)
                
                snippet = ""
                if bs_lib:
                    soup = bs_lib(text_content, 'html.parser')
                    # Tenta pegar o parágrafo onde o processo foi citado
                    for p in soup.find_all(['p', 'div']):
                        if process_num and process_num in p.get_text():
                            snippet = f"<p><i>Contexto: {p.get_text()[:300]}...</i></p>"
                            break
                
                return snippet, process_num
        except Exception as e:
            _logger.error("### OSINT Deep Search Error: %s", str(e))
        return "", False

    def _extract_process_numbers(self, text):
        """
        Usa Regex para encontrar o padrão CNJ: NNNNNNN-NN.NNNN.N.NN.NNNN
        """
        # Regex padrão CNJ
        pattern = r'\b\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b'
        matches = re.findall(pattern, text)
        return matches[0] if matches else False

    def _extract_relevant_data(self, html_content, query, bs_lib):
        """
        Extrai snippets e URLs jurídicas REAIS (Filtrando Ads do Bing/Microsoft).
        """
        if not bs_lib:
            return f"<p>Conexão bem sucedida para {query}. (Instale BS4)</p>", []
        
        soup = bs_lib(html_content, 'html.parser')
        found_info = []
        found_urls = []
        
        # Filtros Anti-Anúncio e Links de Rastreamento
        noise_keywords = ['viewing ads', 'privacy protected', 'microsoft', 'advertisement', 'patrocinado', 'anúncio']
        ad_trackers = ['ad_provider', 'aclick', 'bing.com', 'y.js', 'doubleclick', 'googleadservices']
        
        # Priorização de domínios jurídicos orgânicos
        legal_domains = ['jusbrasil.com.br', 'escavador.com', 'tj.jus.br', 'trf', 'pje', 'migalhas', 'conjur']

        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text().strip()
            
            if any(noise in text.lower() for noise in noise_keywords): continue
            if any(tracker in href for tracker in ad_trackers): continue

            if any(domain in href for domain in legal_domains):
                if len(text) > 15:
                    found_info.append(f"<b>[Link Jurídico]</b> <a href='{href}' target='_blank'>{text}</a>")
                    if href.startswith('http'):
                        found_urls.append(link['href'])

        for tag in soup.find_all(['div', 'span', 'p']):
            text = tag.get_text().strip()
            if any(noise in text.lower() for noise in noise_keywords): continue
            if any(term in text.lower() for term in ['processo', 'tribunal', 'diário oficial', 'justiça', 'direito', 'tj-']):
                if 40 < len(text) < 400 and text not in found_info:
                    if not any(text[:30] in str(existing) for existing in found_info):
                        found_info.append(text)
        
        if not found_info:
            return f"<p>Busca concluída para <b>{query}</b>, sem resultados úteis.</p>", []
            
        html = "<ul>"
        for info in found_info[:8]: html += f"<li>{info}</li>"
        html += "</ul>"
        return html, found_urls

    def _cron_check_targets(self):
        """
        Método chamado pelo CRON para verificar alvos ativos.
        """
        targets = self.search([('state', '=', 'active')])
        for target in targets:
            target.action_check_now()
