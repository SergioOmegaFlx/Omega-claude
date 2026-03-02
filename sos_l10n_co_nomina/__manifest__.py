
{
    'name': "Localización Nómina Colombiana",

    'summary': """
        Localización Nomina Colombiana""",

    'description': """
        Localización Nomina Colombiana""",

    'author': "Soluciones Open Source",
    'website': "https://www.solucionesos.com",

    'category': 'Payroll',
    'version': '0.1',

    'countries': ['co'],
    # any module necessary for this one to work correctly
    'depends': ['base','hr_payroll','hr_holidays','sos_nomina','sos_nomina_ss','sos_nomina_ps','contacts',],

    # always loaded
    'data': [
        'data/hr_structure.xml',
        'data/hr_rule_category.xml',
        'data/hr_rules.xml',
        'data/hr_worked_entry_type.xml', 
        'data/hr_input_type.xml',
        'data/hr_leave_type.xml',
        'data/hr_leave_accrual_plan.xml',
        'data/hr_leave_accrual_level.xml',
        'data/hr_settlement_structure.xml',
        'views/hr_pila_views.xml',
        'wizard/pila_asiento_wizard_view.xml',  
    ],
    # only loaded in demonstration mode   
}