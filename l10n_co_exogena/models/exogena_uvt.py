# -*- coding: utf-8 -*-
from odoo import models, fields

class ExogenaUvt(models.Model):
    _name = 'exogena.uvt'
    _description = 'Valor de la UVT por Año Fiscal'
    _order = 'year desc'

    year = fields.Integer(string="Año", required=True, index=True)
    value = fields.Float(string="Valor UVT", required=True, digits=(16, 2))
    company_id = fields.Many2one(
        'res.company',
        string="Compañía",
        required=True,
        default=lambda self: self.env.company
    )

    _sql_constraints = [
        ('year_company_uniq', 'unique (year, company_id)', 'Solo puede definir un valor de UVT por año y compañía.')
    ]