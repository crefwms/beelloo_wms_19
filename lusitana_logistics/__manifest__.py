# -*- coding: utf-8 -*-
{
    'name': "Lusitana Logística",
    'summary': "Módulo customizado para gestão de logística da Lusitana, incluindo Apresentação de Veículos e controle de pátio e checklists.",
    'description': """
        Módulo abrangente para otimizar os processos logísticos da Lusitana,
        focado inicialmente na gestão da entrada e saída de veículos,
        com controle de marcação, cadastro detalhado de motoristas e veículos,
        controle de lacres, e preparação para integração com agenda Heineken e checklists.
    """,
    'author': "Medoo",
    #'website': "http://www.suaempresa.com.br",
    'category': 'Operations/Logistics',
    'version': '18.0.1.1.1',
    'depends': ['base', 'stock', 'hr', 'mail', 'contacts', 'fleet', 'board'],
    'assets': {
        'web.assets_backend': [
        ],
    },
    'data': [
        'security/lusitana_logistics_security.xml',
        'security/ir.model.access.csv',
        'data/zebra_template_data.xml',
        'data/ir_sequence_data.xml',

        'views/agenda_import_wizard_views.xml',

        'views/vehicle_type_views.xml',
        'views/body_type_views.xml',
        'views/tie_type_views.xml',
        'views/tightening_type_views.xml',
        'views/operation_type_views.xml',
        'views/priority_views.xml',

        'views/res_partner_views.xml',
        'views/vehicle_views.xml',
        'views/lacre_views.xml',
        'views/agenda_views.xml',
        
        # 'views/check_list_views.xml',         # Próximos passos
        # 'views/check_list_item_views.xml',    # Próximos passos
        'views/vehicle_presentation_views.xml',
        'views/lacre_batch_wizard_views.xml',
        'reports/checklist_report.xml',
        'views/menu_views.xml',
        'views/dashboard_views.xml',
        'views/checklist_views.xml',
        'reports/vehicle_presentation_report.xml',
        'views/presentation_checklist_views.xml',
        'views/checklist_generator_wizard_views.xml',
        
    ],
    'demo': [], # Dados de demonstração, se houver
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}