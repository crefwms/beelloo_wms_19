1. O Script: Briefing para o Antigravity
Copie e cole este comando para iniciar a construção com o Antigravity:

"Antigravity, vamos construir um módulo para Odoo 18 chamado legal_osint_target. O objetivo é monitorar processos judiciais. O módulo deve permitir cadastrar 'Alvos' (nomes ou CPFs), definir a frequência de busca e armazenar os resultados encontrados. Use o padrão Odoo 18: substitua views tree por list, e utilize apenas a nova sintaxe de atributos dinâmicos no XML (sem o antigo attrs)."

2. Estrutura de Pastas (Boilerplate)
Aqui está como o Antigravity deve organizar os arquivos na sua instância:

Plaintext
legal_osint_target/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── osint_target.py       # Onde definimos o que monitorar
│   └── osint_result.py       # Onde salvamos o que o robô encontrou
├── views/
│   ├── osint_target_views.xml
│   ├── osint_result_views.xml
│   └── menu_views.xml
└── security/
    └── ir.model.access.csv
3. Código Base (A Lógica para o Antigravity Processar)
Aqui está o "esqueleto" técnico que você deve passar para ele gerar:

A. O Modelo (osint_target.py)
Python
from odoo import models, fields, api

class OsintTarget(models.Model):
    _name = 'osint.target'
    _description = 'Alvo de Monitoramento Jurídico'

    name = fields.Char(string='Nome do Alvo/Processo', required=True)
    identifier = fields.Char(string='CPF/CNPJ ou Nº Processo')
    state = fields.Selection([
        ('draft', 'Rascunho'),
        ('active', 'Monitorando'),
        ('paused', 'Pausado')
    ], default='draft', string='Status')
    
    last_check = fields.Datetime(string='Última Verificação', readonly=True)
    next_check = fields.Datetime(string='Próxima Verificação')
    
    result_ids = fields.One2many('osint.result', 'target_id', string='Resultados Encontrados')

    def action_check_now(self):
        # Aqui entrará o seu script Python de WebScraping no futuro
        pass
B. A View (Exemplo Odoo 18 - osint_target_views.xml)
Note o uso de list e a ausência de attrs:

XML
<record id="view_osint_target_list" model="ir.ui.view">
    <field name="name">osint.target.list</field>
    <field name="model">osint.target</field>
    <field name="arch" type="xml">
        <list string="Alvos de Monitoramento">
            <field name="name"/>
            <field name="identifier"/>
            <field name="state" widget="badge" decoration-info="state == 'active'"/>
            <field name="last_check"/>
        </list>
    </field>
</record>
4. Interagindo com o Antigravity para Refinar
Depois que ele gerar a estrutura básica, você deve dar os seguintes comandos de "refino":

Para a automação: "Antigravity, crie um ir.cron que execute o método action_check_now a cada 24 horas para todos os targets com state 'active'."

Para a inteligência: "Agora, adicione um campo HTML no modelo osint.result para salvar o resumo do andamento processual capturado pelo robô."