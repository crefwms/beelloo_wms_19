{
    'name': 'Rastreabilidade HNK',
    'version': '18.0.1.0.0',
    'summary': 'Controle de rastreabilidade de etiquetas e DTs',
    'category': 'Inventory',
    'author': 'Cassiano/ CR & F',
    'depends': ['base', 'product', 'contacts', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/veiculo_views.xml',
        'views/rastreabilidade_dt_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}