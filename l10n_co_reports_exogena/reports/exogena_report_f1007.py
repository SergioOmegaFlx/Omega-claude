# -*- coding: utf-8 -*-
from odoo import models,api, _

class ExogenaReportF1007(models.Model):
    """Formato 1007: Ingresos Recibidos"""
    _name = 'exogena.report.f1007'
    _description = 'Formato 1007 - Ingresos'
    _inherit = 'exogena.report.base'
    
    def _get_formato_code(self):
        return '1007'
    
    def _get_column_keys(self):
        return ['ingresos', 'devoluciones']
    
    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': '', 'class': 'text'},
            {'name': _('Ingresos Brutos'), 'class': 'number'},
            {'name': _('Devoluciones'), 'class': 'number'},
        ]
