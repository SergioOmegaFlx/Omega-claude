# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ExogenaFormato(models.Model):
    """Formatos de Información Exógena DIAN"""
    _name = 'exogena.formato'
    _description = 'Formato de Información Exógena'
    _order = 'code'

    code = fields.Char(
        string='Código',
        required=True,
        help='Código del formato DIAN (ej: 1001, 1003, etc.)'
    )
    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre descriptivo del formato'
    )
    version = fields.Char(
        string='Versión',
        default='10',
        help='Versión del formato según DIAN'
    )
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    tipo_dato = fields.Selection([
        ('flujo', 'Flujo (Débito - Crédito durante período)'),
        ('saldo', 'Saldo (Posición al final del período)'),
    ], string='Tipo de Dato', required=True, default='flujo',
       help='Define si el formato reporta movimientos del período o saldos finales')
    
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción detallada del formato y su propósito'
    )
    
    concepto_ids = fields.One2many(
        'exogena.concepto',
        'formato_id',
        string='Conceptos'
    )
    
    _sql_constraints = [
        ('code_version_uniq', 'unique(code, version)', 
         'Ya existe un formato con este código y versión.')
    ]
    
    def name_get(self):
        result = []
        for rec in self:
            name = f"[{rec.code}] {rec.name}"
            if rec.version:
                name += f" v.{rec.version}"
            result.append((rec.id, name))
        return result