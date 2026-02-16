# -*- coding: utf-8 -*-
from odoo import models,api, _

class ExogenaReportF1006(models.Model):
    """Formato 1006: IVA Generado"""
    _name = 'exogena.report.f1006'
    _description = 'Formato 1006 - IVA Generado'
    _inherit = 'exogena.report.base'
    
    def _get_formato_code(self):
        return '1006'
    
    def _get_column_keys(self):
        return ['iva_generado', 'devoluciones']
    
    @api.model
    def _get_columns_name(self, options):
        return [
            {'name': '', 'class': 'text'},
            {'name': _('IVA Generado'), 'class': 'number'},
            {'name': _('Devoluciones en Ventas'), 'class': 'number'},
        ]
