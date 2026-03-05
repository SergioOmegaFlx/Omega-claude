# -*- coding: utf-8 -*-
from odoo import models, fields

class HrRecargoType(models.Model):
    _name = 'hr.recargo.type'
    _description = 'Surcharge Type (Recargo)'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    percent = fields.Float(string='Percentage (%)', required=True, help="The percentage to apply for this surcharge type.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "The code for the surcharge type must be unique!"),
    ]