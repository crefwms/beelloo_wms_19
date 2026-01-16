{
    'name': 'Beeloo WMS - Outbound (Expedição)',
    'version': '18.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Gestão de expedição, picking FEFO e regras de Shelf Life por cliente.',
    'author': 'Lusitana / Beeloo',
    'website': 'https://www.suaempresa.com',
    'depends': [
        'beeloo_wms_internal', # Depende do Pilar 3
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/outbound_sequences.xml', # Para o 'shelf.life.flow'
        'views/res_partner_views.xml', # Onde a política será configurada
        'views/shelf_life_flow_views.xml', # O "Flow" de exceção
        'views/shelf_life_wizard_views.xml', # O "Tabelão"
        'wizard/outbound_report_wizard_view.xml',
        'views/outbound_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}