{
    'name': 'Beeloo Reverse Logistics',
    'version': '18.0.1.0.0',
    'summary': 'Advanced Reverse Logistics for High-Volume E-commerce (Magalu, ML, Amazon)',
    'description': """
        Enterprise Reverse Logistics Module:
        - RMA Management
        - Operational Safety Checklists
        - Marketplace SLA Tracking
        - A/B/C Grading System
        - Control Tower Dashboard
        - Integration with Driver Portal (FastAPI)
    """,
    'author': 'Beeloo',
    'category': 'Inventory/Inventory',
    'depends': ['stock', 'sale', 'fleet'],
    'data': [
        'security/ir.model.access.csv',
        'data/stock_data.xml',
        'data/safety_data.xml',
        'views/rma_views.xml',
        'views/safety_views.xml',
        'views/grading_views.xml',
        'views/control_tower_views.xml',
        'views/batch_views.xml',
        'views/menu_views.xml',
        'reports/rma_reports.xml',
        'reports/rma_templates.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
