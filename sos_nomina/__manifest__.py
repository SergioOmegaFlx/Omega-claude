
{
    'name': "Nomina",

    'summary': """
        Nomina management""",

    'description': """
        Nomina management
    """,

    'author': "Táctica",
    'website': "http://www.puntosdeventa.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_contract','hr_payroll','hr_work_entry_contract_enterprise'],

    # always loaded
    'data': [
        'views/views.xml',
        
    ],
    # only loaded in demonstration mode
    
}