{
    'name': 'Beeloo WMS - Operações Internas',
    'version': '18.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Gestão de movimentações internas, inventário, avarias e retrabalho.',
    'author': 'Cassiano Cavalciuk / CREF',
    'website': 'https://www.cref.com.br',
    'depends': [
        'base',
        'mail', 
        'stock',
        'stock_account',
        'beeloo_wms_base',
        'beeloo_wms_presentation',
    ],
    'data': [
        'security/ir.model.access.csv',
        
        # --- ARQUIVOS FALTANTES (DATA) ---
        'data/internal_sequences.xml',      # (Você precisa criar este arquivo)
        'data/internal_cron_jobs.xml',      # (Este você já tinha)
        
        # --- ARQUIVOS FALTANTES (REPORT) ---
        'report/damage_report_template.xml', # (Você precisa criar este arquivo)
        
        # --- ARQUIVOS FALTANTES (VIEWS) ---
        'views/internal_menus.xml',            # (Menu "Operações Internas")
        
        # --- ORDEM CORRIGIDA ---
        
        # 1. Carrega o Wizard (que CRIA a ação 'action_damage_report_wizard')
        'views/damage_report_wizard_views.xml', 
        
        # 2. Carrega o Picking (que USA a ação)
        'views/stock_picking_views.xml',

        'views/consolidation_wizard_view.xml',
        'views/stock_quant_views.xml', 
        
        # --- FIM DA CORREÇÃO ---
        
        'views/damage_report_views.xml',       # (A tela do "BO" principal)
        'views/stock_picking_type_views.xml',  # (Este você já tinha)
        'views/rework_views.xml',              # (Este você já tinha)
        'views/beeloo_cycle_count_views.xml',  # (A tela do "Plano de Contagem")
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}