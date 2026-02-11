# -*- coding: utf-8 -*-
{
    'name': "Información Exógena para Colombia (DIAN)",
    'summary': """
        Módulo integral para la generación de reportes de Información Exógena
        Tributaria requeridos por la DIAN en Colombia.
    """,
    'description': """
        - Asistente para la generación de formatos de exógena.
        - Modelos de datos configurables para conceptos y mapeos de cuentas.
        - Generación en segundo plano para alto volumen de datos.
        - Exportación a formato XML compatible con el prevalidador de la DIAN.
        - Formato Inicial: 1001 v.10
    """,
    'author': "Sergio Alberto Perez Plata",
    'website': "",
    'category': 'Accounting/Localizations',
    'version': '18.0.1.0.0',
    'depends': ['account', 'l10n_co'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/exogena_format_data.xml',
        
        # 1. Cargar TODAS las vistas de modelos y wizards PRIMERO
        'views/exogena_format_views.xml',
        'views/exogena_concepto_views.xml',
        'views/exogena_concepto_mapping_views.xml',
        'views/exogena_uvt_views.xml',
        'views/exogena_report_views.xml',
        'wizards/exogena_generation_wizard_views.xml',
        
        # 2. Cargar el archivo de menús DESPUÉS, para que encuentre las acciones
        'views/exogena_menus.xml',
    ],
    'license': 'OEEL-1',
}