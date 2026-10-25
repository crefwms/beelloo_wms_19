{
    'name': 'Monitoramento WMS - Dashboard Logística',
    'version': '18.0.1.0.0',
    'summary': 'KPIs de TRT e Conexão SQL Server Legado',
    'description': """
        Módulo de Dashboard para o Beeloo WMS.
        Funcionalidades:
        - Conexão com banco de dados SQL Server legado (Portaria).
        - Importação de dados de movimentação.
        - Cálculo de TRT (Turnaround Time) e eficiência operacional.
        - Gráficos e Listas de KPIs.
    """,
    'category': 'Inventory/Logistics',
    'author': 'Cassiano - CR & F',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'beeloo_wms_base'],
    
    # Arquivos que o Odoo deve carregar (na ordem correta)
    'data': [
        'security/ir.model.access.csv',
        'views/logistica_kpi_views.xml',
        'data/ir_cron.xml',
    ],
    
    # Importante: Avisa ao Odoo que este módulo precisa do pyodbc
    'external_dependencies': {
        'python': ['pyodbc'],
    },

    # Define se é um aplicativo principal no menu Apps
    'application': True,
    'installable': True,
    'auto_install': False,
}