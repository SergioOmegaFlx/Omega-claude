# -*- coding: utf-8 -*-
from odoo import models,api, _

class ExogenaReportF1005(models.Model):
    """Formato 1005: IVA Descontable"""
    _name = 'exogena.report.f1005'
    _description = 'Formato 1005 - IVA Descontable'
    _inherit = 'exogena.report.base'
    
    def _get_formato_code(self):
        return '1005'
    
    def _get_column_keys(self):
        return ['iva_descontable', 'devoluciones']
    
    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': '', 'class': 'text'},
            {'name': _('IVA Descontable'), 'class': 'number'},
            {'name': _('Devoluciones en Compras'), 'class': 'number'},
        ]
