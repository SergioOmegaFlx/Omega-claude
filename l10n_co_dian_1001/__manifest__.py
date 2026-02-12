{
    "name": "DIAN Exógena Formato 1001 - Colombia",
    "version": "1.0",
    "author": "Sergio Perez",
    "license": "LGPL-3",
    "category": "Accounting/Localizations",
    "summary": "Reporte Información Exógena DIAN - Formato 1001",
    "depends": [
        "base",
        "account",
        "l10n_co",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/dian_1001_report_templates.xml",
        "views/dian_concepto_mapping_views.xml",
        "views/dian_report_wizard_views.xml",
    ],
    "installable": True,
    "application": False,
}
