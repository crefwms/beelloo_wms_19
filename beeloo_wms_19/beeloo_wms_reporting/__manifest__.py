# /beeloo_wms_reporting/__manifest__.py
{
    'name': 'Beeloo WMS - Reporting',
    'version': '18.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Dashboard e KPIs do WMS (Abordagem "Motor" + "Vitrine")',
    'author': 'Lusitana / Beeloo',
    'website': 'https://www.suaempresa.com',
    'depends': [
        'beeloo_wms_base', # Onde os campos de KPI (Pilar 0) estão
        'stock',
        'board',
    ],
    'data': [
        # Carregando APENAS o CSV.
        # Todos os XMLs de 'data' e 'views' estão desativados.
        'security/ir.model.access.csv',
        'data/reporting_cron_jobs.xml',
        'views/wms_kpi_history_views.xml',
        'views/wms_dashboard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}