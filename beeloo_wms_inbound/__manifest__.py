{
    'name': 'Beeloo WMS - Inbound (Recebimento)',
    'version': '18.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Gestão do recebimento, importação de XML NFe, geração de lotes e endereçamento.',
    'author': 'Lusitana / Beeloo',
    'website': 'https://www.suaempresa.com',
    'depends': [
        'beeloo_wms_base',
        'beeloo_wms_presentation', # Dependemos DIRETAMENTE do Pilar 1
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml', # Vamos adicionar botões no Recebimento
        'views/inbound_view.xml',
        'views/beeloo_scanner_view.xml',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
} # type: ignore