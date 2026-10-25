{
    'name': 'Legal OSINT Target',
    'version': '18.0.1.0.0',
    'summary': 'Monitoramento de processos judiciais para alvos específicos',
    'description': """
        Módulo para monitoramento de alvos (nomes/CPFs) em processos judiciais.
        Permite definir alvos, frequência de busca e armazenar resultados de OSINT.
    """,
    'category': 'Legal',
    'author': 'Cassiano',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'security/legal_osint_security.xml',
        'data/ir_cron.xml',
        'views/osint_result_views.xml',
        'views/osint_target_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
}
