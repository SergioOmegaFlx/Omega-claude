# -*- coding: utf-8 -*-
from odoo import models,api, _

class ExogenaReportF1003(models.Model):
    """Formato 1003: Retenciones en la fuente que le practicaron"""
    _name = 'exogena.report.f1003'
    _description = 'Formato 1003 - Retenciones Practicadas'
    _inherit = 'exogena.report.base'
    
    def _get_formato_code(self):
        return '1003'
    
    def _get_column_keys(self):
        return ['base', 'retencion']
    
    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': '', 'class': 'text'},
            {'name': _('Valor Base'), 'class': 'number'},
            {'name': _('Valor Retenido'), 'class': 'number'},
        ]
