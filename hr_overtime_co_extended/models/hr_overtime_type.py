# -*- coding: utf-8 -*-
from odoo import models, fields

class HrOvertimeType(models.Model):
    _name = 'hr.overtime.type'
    _description = 'Overtime Type'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    percent = fields.Float(string='Percentage (%)', required=True, help="The percentage to apply for this overtime type.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "The code for the overtime type must be unique!"),
    ]