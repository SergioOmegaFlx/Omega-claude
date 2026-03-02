# -*- coding: utf-8 -*-
{
    'name': "sos_nomina_ps",
    'summary': "Liquidación de Prestaciones Sociales",
    'description': "Módulo para la liquidación de prestaciones sociales en Odoo.",
    'author': "Táctica",
    'website': "http://www.solucionesos.com",
    'category': 'Human Resources/Payroll',
    'version': '18.0.1.0',
    'depends': ['hr_payroll'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/products.xml',
        'views/views.xml',
    ],
    'installable': True,
    'application': False,
}
