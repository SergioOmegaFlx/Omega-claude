# -*- coding: utf-8 -*-
from odoo import models,api, _

class ExogenaReportF1008(models.Model):
    """Formato 1008: Saldos CxC"""
    _name = 'exogena.report.f1008'
    _description = 'Formato 1008 - Cuentas por Cobrar'
    _inherit = 'exogena.report.base'
    
    def _get_formato_code(self):
        return '1008'
    
    def _get_column_keys(self):
        return ['saldo']
    
    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': '', 'class': 'text'},
            {'name': _('Saldo al Corte'), 'class': 'number'},
        ]
