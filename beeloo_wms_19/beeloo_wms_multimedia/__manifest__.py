{
    'name': 'Beeloo WMS - Multimedia & Evidence',
    'version': '18.0.1.0.0',
    'category': 'Warehouse',
    'summary': 'Captura de evidências (Vídeo/Foto) para Portaria e Picking',
    'depends': [
        'base',
        'stock',
        'beeloo_wms_inbound',
        'beeloo_wms_outbound',
        'beeloo_wms_base', 
        'beeloo_wms_presentation', 
        # Nota: Não precisa depender estritamente de inbound/outbound se o campo
        # x_document_ids estiver definido em um modelo base ou se usarmos 
        # verificação dinâmica, mas idealmente depende de quem define x_document_ids.
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/video_wizard_view.xml',
    ],
    'installable': True,
    'application': False, # É um módulo técnico/suporte
}