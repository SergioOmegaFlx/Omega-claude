{
    "name": "CO Payroll Bridge: Overtime/Recargos → Work Entries",
    "version": "1.0",
    "summary": "Puente entre hr_overtime_co_extended y sos_l10n_co_nomina (hr.work.entry).",
    "category": "Human Resources/Payroll",
    "license": "LGPL-3",
    "author": "Sergio Alberto Perez Plata",
    "depends": [
        "hr",
        "hr_attendance",
        "hr_contract",
        "hr_work_entry",
        "hr_payroll",
        "hr_overtime_co_extended",   # TU módulo (intocable)
        "sos_l10n_co_nomina",        # Motor del partner
    ],
    "data": [
    "views/hr_attendance_views.xml",
    ],
    "installable": True,
    "application": False,
}
