{
    'name': 'Beeloo WMS - Base',
    'version': '18.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Módulo base para o WMS Beeloo. Adiciona campos core para produtos e localizações.',
    'author': 'Lusitana / Beeloo',
    'website': 'https://www.suaempresa.com',
    'depends': [
        'base',
        'stock',  # Dependemos do módulo de estoque
        'product', # E do módulo de produto
    ],
    'data': [
        'security/ir.model.access.csv', # (Vamos precisar criar este)
        'views/stock_warehouse_views.xml',
        'views/product_template_views.xml',
        'views/stock_location_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}