{
    'name': 'OEA Management',
    'version': '18.0.1.0.0',
    'category': 'Operations',
    'summary': 'Assistência na certificação OEA (Operador Econômico Autorizado)',
    'description': """
        Módulo para auxiliar no processo de certificação OEA.
        - Gestão de requisitos normativos (IN RFB 1.985/2020)
        - Acompanhamento de conformidade (Auditorias)
        - Repositório de evidências
    """,
    'author': 'Cassiano Cavalciuk / Medoo',
    'website': 'https://medoo.dev',
    'depends': ['base', 'mail', 'web', 'stock', 'hr', 'product'],
    'data': [
        'security/oea_security_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/oea_cron_data.xml',
        'views/oea_requirement_views.xml',
        'views/oea_audit_views.xml',
        'views/oea_requirement_item_views.xml',
        'views/oea_dashboard_view.xml',
        'views/oea_sgsi_views.xml',
        'views/oea_risk_views.xml',
        'wizard/oea_import_trello_views.xml',
        'wizard/oea_report_views.xml',
        'views/menu_views.xml',
        'report/oea_report_templates.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
