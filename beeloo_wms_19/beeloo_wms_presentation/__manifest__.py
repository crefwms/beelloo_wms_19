{
    'name': 'Beeloo WMS - Apresentação (Portaria)',
    'version': '18.0.1.0.0',
    'category': 'Warehouse Management',
    'summary': 'Controla o "portão" (gate) de entrada e saída de veículos e o processo de troca de NF.',
    'author': 'Lusitana / Beeloo',
    'website': 'https://www.suaempresa.com',
    'depends': [
        'beeloo_wms_base',  # Nosso alicerce!
        'stock',            # Precisamos do módulo de estoque
        'website',
    ],
    'data': [
    'security/ir.model.access.csv',
    'data/beeloo_presentation_sequence.xml',

    # --- O "PAI" DEVE VIR PRIMEIRO ---
    'views/beeloo_presentation_views.xml',   # <-- O "PAI" (Cria o menu 'menu_beeloo_wms_root')
    # -----------------------------------

    # Agora os "filhos" podem ser carregados:
    'views/beeloo_configuration_menus.xml',  # <-- O "FILHO"
    'views/beeloo_vehicle_views.xml',
    'views/beeloo_vehicle_types_views.xml',
    'views/beeloo_operation_views.xml',
    'views/stock_picking_views.xml',
    'views/beeloo_agenda_views.xml',
    'views/beeloo_lacre_views.xml',
    'views/landing_page.xml',
    ],
    'installable': True,
    'application': True, # Este é um "App" em si
    'auto_install': False,
    'license': 'LGPL-3',
}