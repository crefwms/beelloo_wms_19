{
    'name': 'Logística Legada (Access)',
    'version': '1.0',
    'summary': 'Visualização de dados do Access via Integração Python',
    'author': 'Cassiano',
    'category': 'Inventory',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/logistica_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}