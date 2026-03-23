{
    'name': 'OMEGA Operations Portal',
    'version': '18.0.1.0.0',
    'category': 'Project',
    'summary': 'Portal de rastreo de operaciones para clientes OMEGA',
    'description': """
        OMEGA Operations Portal
        =======================
        
        Módulo para gestionar el portal de tracking de operaciones logísticas:
        
        * Creación automática de proyectos (DO) desde órdenes de venta
        * Plantillas diferenciadas: Flexitanque, Isotanque, Importación, Op. Física
        * Sistema de visibilidad dual: Tareas internas vs Hitos del cliente
        * Notificaciones automáticas al completar hitos
        * Dashboard de seguimiento en portal del cliente
        * Gestión de alertas y novedades operativas
        
        Desarrollado para OMEGA Internacional - ISO Tanks & Flexitanks
    """,
    'author': 'Sergio Alberto Perez Plata',
    'license': 'LGPL-3',
    'depends': [
        'sale_management',
        'project',
        'sale_project',
        'portal',
        'mail',
    ],
    'data': [
        # Security
        'security/omega_operations_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/project_tags_data.xml',
        'data/project_stages_data.xml',
        'data/project_templates_data.xml',
        # Views
        'views/project_views.xml',
        'views/sale_order_views.xml',
        'views/portal_templates.xml',
        # Automated Actions (load last)
        'data/automated_actions.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'omega_operations_portal/static/src/css/portal_operations.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
