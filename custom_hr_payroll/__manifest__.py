{
    'name': 'Custom HR Payroll',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Campos personalizados para retenciones salariales en Colombia',
    'author': 'Tactica Web',
    'depends': ['hr', 'hr_payroll'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
}
