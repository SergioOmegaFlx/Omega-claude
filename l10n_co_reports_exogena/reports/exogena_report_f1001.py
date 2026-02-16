# -*- coding: utf-8 -*-
from odoo import models, api, _


class ExogenaReportF1001(models.AbstractModel):
    """
    Formato 1001 - Costos y Gastos
    """
    _name = 'exogena.report.f1001'
    _description = 'Formato 1001 - Costos y Gastos'
    _inherit = 'account.report'

    # Código del reporte (OBLIGATORIO)
    def _get_report_name(self):
        return _('Formato 1001 - Costos y Gastos')

    def _get_report_code(self):
        return 'exogena_f1001'

    def _get_columns_name(self, options):
        return [
            {'name': _('Tercero'), 'class': 'text'},
            {'name': _('Pago o Abono Deducible'), 'class': 'number'},
            {'name': _('Pago o Abono No Deducible'), 'class': 'number'},
            {'name': _('Retención en la Fuente'), 'class': 'number'},
        ]

    def _get_lines(self, options, line_id=None):
        # Placeholder funcional para evitar errores
        return []
