# -*- coding: utf-8 -*-
from odoo import models, fields

class ExogenaConcepto(models.Model):
    _name = 'exogena.concepto'
    _description = 'Concepto de Información Exógena DIAN'
    _order = 'code'

    code = fields.Char(string="Código de Concepto", required=True, index=True)
    name = fields.Char(string="Nombre del Concepto", required=True)
    format_id = fields.Many2one(
        'exogena.format',
        string="Formato",
        required=True,
        ondelete='cascade'
    )
    threshold_uvt = fields.Float(
        string="Tope en UVT",
        help="Tope mínimo en UVT para reportar a un tercero por este concepto. Dejar en 0 si no aplica."
    )
    
    _sql_constraints = [
        ('code_format_uniq', 'unique (code, format_id)', 'El código del concepto debe ser único por formato.')
    ]