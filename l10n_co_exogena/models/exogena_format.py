# -*- coding: utf-8 -*-
from odoo import models, fields

class ExogenaFormat(models.Model):
    _name = 'exogena.format'
    _description = 'Formato de Información Exógena'
    _order = 'code'

    code = fields.Char(string="Código", required=True)
    name = fields.Char(string="Nombre del Formato", required=True)
    version = fields.Char(string="Versión")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_version_uniq', 'unique (code, version)', 'Ya existe un formato con este código y versión.')
    ]

    def name_get(self):
        result = []
        for rec in self:
            name = f"[{rec.code}] {rec.name} (v.{rec.version})"
            result.append((rec.id, name))
        return result