# -*- coding: utf-8 -*-
from odoo import models,api, _

class ExogenaReportF1009(models.Model):
    """Formato 1009: Saldos CxP"""
    _name = 'exogena.report.f1009'
    _description = 'Formato 1009 - Cuentas por Pagar'
    _inherit = 'exogena.report.base'
    
    def _get_formato_code(self):
        return '1009'
    
    def _get_column_keys(self):
        return ['saldo']
    
    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': '', 'class': 'text'},
            {'name': _('Saldo al Corte'), 'class': 'number'},
        ]
