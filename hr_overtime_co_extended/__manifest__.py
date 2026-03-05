# -*- coding: utf-8 -*-
{
    'name': "HR Overtime - Colombian Extension",
    'summary': "Cálculo y gestión de horas extra para Colombia con notificaciones.",
    'description': """
Este módulo extiende las siguientes funciones:
- Cálculo automático de horas extra (diurnas, nocturnas, dominicales y festivas).
- Cálculo automático de recargos (nocturnos, dominicales y festivos).
- Tipos de horas extra y recargos configurables.
- Integración con el sistema de asistencia y contratos de RR. HH.
- Cálculos con feriados de Colombia.
    """,
    'author': "Sergio Alberto Perez Plata",
    'category': 'Human Resources/Attendances',
    'version': '18.0.1.0.0',
    'depends': ['web', 'hr_attendance', 'hr_contract', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_security.xml',
        'data/hr_overtime_type.xml',
        'data/hr_recargo_type.xml',
        'data/mail_activity_type.xml',
        'data/ir_cron_data.xml',
        'views/hr_overtime_views.xml',
        'views/hr_recargo_views.xml',
        'views/hr_attendance_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_employee_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_overtime_co_extended/static/src/css/attendance.css',
            'hr_overtime_co_extended/static/src/js/attendance_systray.js',
            'hr_overtime_co_extended/static/src/js/attendance_alert.js',
            'hr_overtime_co_extended/static/src/xml/attendance_alert.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['holidays'],
    },
}