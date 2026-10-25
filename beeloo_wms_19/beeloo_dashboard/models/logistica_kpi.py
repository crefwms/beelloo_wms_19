from odoo import models, fields, api
import pyodbc
from datetime import datetime
import pytz

# --- LISTA OFICIAL DE STATUS ---
STATUS_LIST = [
    ('Agendado', 'Agendado'), ('Portaria', 'Portaria'), ('Entrada', 'Entrada'),
    ('Entrada ATO', 'Entrada ATO'), ('Saída ATO', 'Saída ATO'), ('Entrada Doca', 'Entrada Doca'),
    ('Início Carregamento', 'Início Carregamento'), ('Término Carregamento', 'Término Carregamento'),
    ('Início Amarração', 'Início Amarração'), ('Término Amarração', 'Término Amarração'),
    ('Retorno ATO', 'Retorno ATO'), ('Liberação', 'Liberação'), ('Saída Portaria', 'Saída Portaria'),
    ('Envio Faturamento', 'Envio Faturamento'), ('Retorno Faturamento', 'Retorno Faturamento'),
    ('Cancelado', 'Cancelado'), ('Devolvido', 'Devolvido'), ('Outros', 'Outros')
]

# --- NOVA TABELA: OBSERVAÇÕES ---
class LogisticaObservacao(models.Model):
    _name = 'beeloo.logistica.observacao'
    _description = 'Observações da Carga'
    _order = 'data_registro desc' # As mais recentes primeiro

    kpi_id = fields.Many2one('beeloo.logistica.kpi', string="Portaria Vinculada", ondelete='cascade')
    
    texto = fields.Text(string="Observação")
    autor = fields.Char(string="Conferente/Autor")
    data_registro = fields.Datetime(string="Data/Hora")

class LogisticaProduto(models.Model):
    _name = 'beeloo.logistica.produto'
    _description = 'Itens da Carga'

    kpi_id = fields.Many2one('beeloo.logistica.kpi', string="Portaria Vinculada", ondelete='cascade')
    codigo_produto = fields.Char(string="Cód. Produto")
    descricao = fields.Char(string="Descrição")
    
    quantidade_prevista = fields.Float(string="Qtd. Prevista")
    quantidade_bipada = fields.Float(string="Qtd. Bipada")
    
    status_item = fields.Selection([('0', '🟢 Ativo'), ('1', '🔴 Cancelado')], string="Status Item", default='0')
    
    progresso = fields.Float(string="Progresso (%)", compute="_compute_progresso", store=True)
    status_execucao = fields.Selection([
        ('nao_iniciado', 'Não Iniciado'), ('iniciado', 'Iniciado (0)'),
        ('andamento', 'Em Andamento'), ('concluido', 'Concluído')
    ], string="Situação", compute="_compute_progresso", store=True)

    @api.depends('quantidade_prevista', 'quantidade_bipada', 'status_item')
    def _compute_progresso(self):
        for rec in self:
            if rec.status_item == '1':
                rec.progresso = 0.0
                rec.status_execucao = 'nao_iniciado'
                continue
            if rec.quantidade_prevista > 0:
                rec.progresso = (rec.quantidade_bipada / rec.quantidade_prevista) * 100
            else:
                rec.progresso = 0.0
            
            if rec.quantidade_bipada == -1: rec.status_execucao = 'nao_iniciado'; rec.progresso = 0.0
            elif rec.quantidade_bipada == 0: rec.status_execucao = 'iniciado'
            elif rec.quantidade_bipada >= rec.quantidade_prevista: rec.status_execucao = 'concluido'
            else: rec.status_execucao = 'andamento'

class LogisticaKPI(models.Model):
    _name = 'beeloo.logistica.kpi'
    _description = 'KPIs de Logística'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'data_portaria desc'
    _rec_name = 'transportadora'

    produto_ids = fields.One2many('beeloo.logistica.produto', 'kpi_id', string="Produtos")
    
    # --- NOVO CAMPO DE RELACIONAMENTO ---
    observacao_ids = fields.One2many('beeloo.logistica.observacao', 'kpi_id', string="Observações")

    # --- IDENTIFICAÇÃO ---
    id_externo = fields.Integer(string="ID Portaria", index=True)
    doc_dt = fields.Char(string="DT", index=True)
    status_desc = fields.Selection(STATUS_LIST, string="Status Atual", default='Agendado')
    transportadora = fields.Char(string="Transportadora")
    placa = fields.Char(string="Placa")
    motorista = fields.Char(string="Motorista")
    cliente_destino = fields.Char(string="Cliente/Destino")
    total_pallets = fields.Integer(string="Pallets")
    doca = fields.Char(string="Doca")

    # --- TIMESTAMPS ---
    data_agendada = fields.Datetime("Agendamento")
    data_portaria = fields.Datetime("1. Chegada Portaria")
    data_entrada = fields.Datetime("2. Entrada Pátio")
    entrada_doca = fields.Datetime("3. Entrada Doca")
    inicio_carregamento = fields.Datetime("4. Início Carreg.")
    fim_carregamento = fields.Datetime("5. Fim Carreg.")
    inicio_amarracao = fields.Datetime("6. Início Amarração")
    fim_amarracao = fields.Datetime("7. Fim Amarração")
    envio_faturamento = fields.Datetime("8. Envio Fat.")
    liberacao = fields.Datetime("9. Liberação")
    data_saida = fields.Datetime("10. Saída Final")

    # --- KPIs ---
    kpi_trt_total = fields.Float("TRT Total", compute="_kpi", store=True, group_operator="avg")
    kpi_pontualidade = fields.Float("Pontualidade (+ Atraso / - Adiantado)", compute="_kpi", store=True, group_operator="avg", help="Chegada - Agendamento")
    kpi_trt_consolidado = fields.Float("TRT Consolidado", compute="_kpi", store=True, group_operator="avg")
    kpi_trt_clean = fields.Float("TRT Clean", compute="_kpi", store=True, group_operator="avg")
    kpi_operacao = fields.Float("Operação", compute="_kpi", store=True, group_operator="avg")
    
    kpi_acolhimento = fields.Float("Acolhimento", compute="_kpi", store=True, group_operator="avg")
    kpi_fila = fields.Float("Fila Doca", compute="_kpi", store=True, group_operator="avg")
    kpi_carregamento = fields.Float("Carregamento", compute="_kpi", store=True, group_operator="avg")
    kpi_amarracao = fields.Float("Amarração", compute="_kpi", store=True, group_operator="avg")
    kpi_documental = fields.Float("Documental", compute="_kpi", store=True, group_operator="avg")

    # Compatibilidade
    trt_horas = fields.Float(related='kpi_trt_total', store=True, string="TRT (Legado)")
    tempo_operacao_min = fields.Float(related='kpi_operacao', store=True, string="Op (Legado)")
    tempo_espera_min = fields.Float(related='kpi_fila', store=True, string="Fila (Legado)")

    @api.depends('data_portaria', 'data_saida', 'entrada_doca', 'fim_amarracao', 'data_entrada',
                 'inicio_amarracao', 'fim_carregamento', 'envio_faturamento', 'liberacao', 'data_agendada')
    def _kpi(self):
        for rec in self:
            def c(f, i): return (f-i).total_seconds()/3600 if f and i else 0.0
            rec.kpi_trt_total = c(rec.data_saida, rec.data_portaria)
            rec.kpi_pontualidade = c(rec.data_portaria, rec.data_agendada)
            rec.kpi_trt_consolidado = c(rec.data_saida, rec.data_agendada)
            rec.kpi_trt_clean = c(rec.data_saida, rec.data_entrada)
            rec.kpi_operacao = c(rec.fim_amarracao, rec.entrada_doca)
            rec.kpi_acolhimento = c(rec.data_entrada, rec.data_portaria)
            rec.kpi_fila = c(rec.entrada_doca, rec.data_entrada)
            rec.kpi_carregamento = c(rec.fim_carregamento, rec.entrada_doca)
            rec.kpi_amarracao = c(rec.fim_amarracao, rec.inicio_amarracao)
            rec.kpi_documental = c(rec.liberacao, rec.envio_faturamento)

    def _convert_tz_br_to_utc(self, dt_naive):
        if not dt_naive: return False
        try: return pytz.timezone('America/Sao_Paulo').localize(dt_naive).astimezone(pytz.UTC).replace(tzinfo=None)
        except: return dt_naive

    def action_sync_sql(self):
        # Mantenha suas credenciais originais aqui
        server = '101.44.201.92'
        database = 'provisorio'
        username = 'provisorio1'
        password = 'Cassiano@1921'
        driver = '{ODBC Driver 18 for SQL Server}'
        
        mapa_status_cod = {1: 'Agendado', 2: 'Portaria', 3: 'Entrada', 4: 'Entrada ATO', 5: 'Saída ATO', 6: 'Entrada Doca', 7: 'Início Carregamento', 8: 'Término Carregamento', 9: 'Início Amarração', 10: 'Término Amarração', 11: 'Retorno ATO', 12: 'Liberação', 13: 'Saída Portaria', 90: 'Envio Faturamento', 91: 'Retorno Faturamento', 98: 'Cancelado', 99: 'Devolvido'}

        try:
            conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;')
            cursor = conn.cursor()
            
            # 1. PAI (Portaria) - Busca Top 500
            cursor.execute("""
                SELECT TOP 500 cad_portaria, dt_transportador_nome, dt_transportador_cavalo, dt_transportador_motorista,
                data_agendamento, data_portaria, inicio_carregamento, termino_carregamento, saida_portaria,
                total_pallets, cliente, dt, status, data_entrada, entrada_doca, inicio_amarracao, termino_amarracao, liberacao, envio_faturamento, doca
                FROM portaria WHERE data_portaria IS NOT NULL AND data_portaria > DATEADD(month, -2, GETDATE()) ORDER BY cad_portaria DESC
            """)
            rows_pai = cursor.fetchall()

            for row in rows_pai:
                cad_id, dt_atual = row[0], str(row[11] or '')
                pai = self.search([('id_externo', '=', cad_id)], limit=1)
                vals_pai = {
                    'id_externo': cad_id, 'transportadora': row[1] or '', 'placa': row[2], 'motorista': row[3],
                    'data_agendada': self._convert_tz_br_to_utc(row[4]), 'data_portaria': self._convert_tz_br_to_utc(row[5]),
                    'inicio_carregamento': self._convert_tz_br_to_utc(row[6]), 'fim_carregamento': self._convert_tz_br_to_utc(row[7]),
                    'data_saida': self._convert_tz_br_to_utc(row[8]), 'total_pallets': row[9] or 0, 'cliente_destino': row[10],
                    'doc_dt': dt_atual, 'status_desc': mapa_status_cod.get(row[12], 'Outros'),
                    'data_entrada': self._convert_tz_br_to_utc(row[13]), 'entrada_doca': self._convert_tz_br_to_utc(row[14]),
                    'inicio_amarracao': self._convert_tz_br_to_utc(row[15]), 'fim_amarracao': self._convert_tz_br_to_utc(row[16]),
                    'liberacao': self._convert_tz_br_to_utc(row[17]), 'envio_faturamento': self._convert_tz_br_to_utc(row[18]),
                    'doca': str(row[19] or '')
                }
                if not pai: pai = self.create(vals_pai)
                else: pai.write(vals_pai)

                if dt_atual:
                    # 2. FILHOS 1: PRODUTOS
                    pai.produto_ids.unlink()
                    cursor.execute("SELECT dt_produto_codigo_produto, dt_produto_produto_descricao, dt_produto_quantidade, status, etiqueta FROM portaria_produto WHERE dt_number = ?", (dt_atual,))
                    rows_prod = cursor.fetchall()
                    lista_produtos = []
                    for prod in rows_prod:
                        val_etiqueta = prod[4]
                        if val_etiqueta is None: qtd_bipada = -1
                        else:
                            try: qtd_bipada = float(val_etiqueta)
                            except: qtd_bipada = 0.0

                        lista_produtos.append((0, 0, {
                            'codigo_produto': str(prod[0]), 'descricao': prod[1], 'quantidade_prevista': prod[2],
                            'status_item': str(prod[3]), 'quantidade_bipada': qtd_bipada
                        }))
                    if lista_produtos: pai.write({'produto_ids': lista_produtos})

                    # 3. FILHOS 2: OBSERVAÇÕES (NOVO!)
                    # ATENÇÃO: Estou assumindo que a tabela se chama 'portaria_obs'. Se for outro nome, mude aqui.
                    pai.observacao_ids.unlink()
                    cursor.execute("""
                        SELECT obsobs, obsconferente, obsdata 
                        FROM portaria_obs 
                        WHERE obsdt = ?
                    """, (dt_atual,))
                    rows_obs = cursor.fetchall()
                    lista_obs = []
                    for obs in rows_obs:
                        lista_obs.append((0, 0, {
                            'texto': obs[0] or '',
                            'autor': obs[1] or 'Sistema',
                            'data_registro': self._convert_tz_br_to_utc(obs[2])
                        }))
                    if lista_obs: pai.write({'observacao_ids': lista_obs})

            conn.close()
            return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {'title': 'Sucesso', 'message': 'Sync OK!', 'type': 'success', 'sticky': False}}
        except Exception as e: raise models.ValidationError(f"Erro SQL: {e}")

    # (Mantenha aqui as funções action_update_legacy e action_delete_legacy igual antes)
    # ...
    # ---------------------------------------------------------
    # FUNÇÕES DE ESCRITA (CUIDADO: ALTERAM O SQL SERVER)
    # ---------------------------------------------------------

    def action_update_legacy(self):
        """ Pega os dados atuais do Odoo e atualiza no SQL Server """
        for rec in self:
            server = '101.44.201.92'
            database = 'provisorio'
            username = 'provisorio1'
            password = 'Cassiano@1921'
            driver = '{ODBC Driver 18 for SQL Server}'
            conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;'
            
            # Mapeamento reverso de Status (Texto -> Código)
            # Se você mudar o status no Odoo, ele volta o número para o SQL
            mapa_status_reverso = {
                'Agendado': 1, 'Portaria': 2, 'Entrada': 3, 'Entrada ATO': 4, 'Saída ATO': 5,
                'Entrada Doca': 6, 'Início Carregamento': 7, 'Término Carregamento': 8,
                'Início Amarração': 9, 'Término Amarração': 10, 'Retorno ATO': 11,
                'Liberação': 12, 'Saída Portaria': 13, 'Envio Faturamento': 90,
                'Retorno Faturamento': 91, 'Cancelado': 98, 'Devolvido': 99
            }
            
            # Pega o código numérico, se não achar, mantém o original (não muda)
            status_cod = mapa_status_reverso.get(rec.status_desc)

            try:
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # QUERY SEGURA (Update)
                # Atualiza Placa, Motorista, Doca e Status baseado no ID
                sql = """
                    UPDATE portaria 
                    SET dt_transportador_cavalo = ?, 
                        dt_transportador_motorista = ?,
                        doca = ?,
                        status = ISNULL(?, status) -- Só muda status se encontrarmos o código
                    WHERE cad_portaria = ?
                """
                
                # Os parâmetros entram na ordem das interrogações (?)
                cursor.execute(sql, (
                    rec.placa, 
                    rec.motorista, 
                    rec.doca, 
                    status_cod, 
                    rec.id_externo
                ))
                
                conn.commit() # Confirma a transação
                conn.close()

                # Log de Segurança no Odoo
                rec.message_post(body=f"✅ Dados atualizados no SQL Server por {self.env.user.name}.")
                
            except Exception as e:
                raise models.ValidationError(f"Erro ao atualizar SQL Server: {e}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Sucesso', 'message': 'Registro atualizado no Legado!', 'type': 'success', 'sticky': False}
        }

    def action_delete_legacy(self):
        """ Apaga o registro no SQL Server e depois no Odoo """
        for rec in self:
            server = '101.44.201.92'
            database = 'provisorio'
            username = 'provisorio1'
            password = 'Cassiano@1921'
            driver = '{ODBC Driver 18 for SQL Server}'
            conn_str = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;'
            
            try:
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()

                # 1. Apaga os Produtos (Filhos) primeiro para não dar erro de chave estrangeira
                # Se sua tabela portaria_produto tiver vínculo, precisa apagar lá antes
                # Se não tiver vínculo forte (FK), pode pular ou fazer por garantia:
                # cursor.execute("DELETE FROM portaria_produto WHERE dt_number = ?", (rec.doc_dt,))

                # 2. Apaga a Portaria (Pai)
                cursor.execute("DELETE FROM portaria WHERE cad_portaria = ?", (rec.id_externo,))
                
                if cursor.rowcount == 0:
                    raise models.ValidationError("O registro já não existe mais no SQL Server.")

                conn.commit()
                conn.close()

                # 3. Apaga do Odoo
                rec.unlink()
                
                # Como apagou do Odoo, não dá pra gravar log no registro, 
                # mas podemos retornar um aviso visual.
                
            except Exception as e:
                raise models.ValidationError(f"Erro ao excluir do SQL Server: {e}")

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Excluído', 'message': 'Registro removido permanentemente do SQL Server.', 'type': 'warning', 'sticky': False}
        }