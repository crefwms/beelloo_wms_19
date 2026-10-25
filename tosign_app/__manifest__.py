{
    'name': 'ToSign - Assinatura de Documentos',
    'version': '18.0.1.0.0',
    'summary': 'Upload e assinatura de documentos PDF, DOC e DOCX',
    'description': """
        Módulo para assinatura digital de documentos.
        Funcionalidades:
        - Upload de arquivos PDF, DOC e DOCX
        - Visualização do documento
        - Assinatura digital na tela
        - Histórico de documentos assinados
    """,
    'category': 'Assinatura de Documentos',
    'author': 'Cassiano - CR & F',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web'],

    'data': [
        'security/ir.model.access.csv',
        'views/tosign_wizard_views.xml',
        'views/tosign_document_views.xml',
        'views/tosign_menu.xml',
        'views/templates/tosign_templates.xml',
    ],

    'application': True,
    'installable': True,
    'auto_install': False,
}
