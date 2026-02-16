# -*- coding: utf-8 -*-
{
    'name': 'Colombia - Reportes de Información Exógena DIAN',
    'version': '1.0',
    'category': 'Accounting/Localizations/Reporting',
    'summary': 'Reportes dinámicos de Información Exógena tributaria para Colombia',
    'description': """
Reportes de Información Exógena DIAN - Colombia
================================================

Este módulo genera reportes dinámicos de Información Exógena requeridos por la DIAN,
utilizando el motor de reportes financieros de Odoo 18 (account.report).

Características principales:
-----------------------------
* Vista dinámica similar al Libro Mayor (expandible por concepto y tercero)
* Formatos soportados: 1001, 1003, 1005, 1006, 1007, 1008, 1009
* Mapeo flexible de cuentas contables a conceptos DIAN
* Soporte para jerarquía de cuentas (drill-down automático)
* Agrupación de cuantías menores (NIT 222222222)
* Filtros nativos de fecha, compañía y períodos
* Optimizado para grandes volúmenes de datos
* Exportación a XLSX con formato DIAN

Formatos implementados:
-----------------------
* 1001: Pagos o abonos en cuenta y retenciones practicadas
* 1003: Retenciones en la fuente que le practicaron
* 1005: Impuesto sobre las ventas descontable (IVA compras)
* 1006: Impuesto sobre las ventas generado (IVA ventas)
* 1007: Ingresos recibidos para terceros
* 1008: Saldos de cuentas por cobrar (CxC)
* 1009: Saldos de cuentas por pagar (CxP)

Requisitos:
-----------
* Odoo 18.0 Enterprise (para account.report)
* Módulo l10n_co (Localización Colombia)
* Códigos DANE configurados en departamentos y municipios
    """,
    'author': 'Sergio Alberto Perez PLata',
    'license': 'OEEL-1',
    'depends': [
        'account_reports',  # Motor de reportes dinámicos de Odoo 18 Enterprise
        'l10n_co',          # Localización Colombia
    ],
    'data': [
        # Seguridad
        'security/ir.model.access.csv',
        
        # Datos base
        'data/exogena_formato_data.xml',
        'data/exogena_concepto_data.xml',
        
        # Vistas de configuración
        'views/exogena_formato_views.xml',
        'views/exogena_concepto_views.xml',
        'views/exogena_concepto_cuenta_views.xml',
        'views/account_account_views.xml',
        
        # Reportes dinámicos
        'reports/exogena_report_f1001.xml',
        'reports/exogena_report_f1003.xml',
        'reports/exogena_report_f1005.xml',
        'reports/exogena_report_f1006.xml',
        'reports/exogena_report_f1007.xml',
        'reports/exogena_report_f1008.xml',
        'reports/exogena_report_f1009.xml',
        
        # Menús
        'views/exogena_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
