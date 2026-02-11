# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ExogenaConceptoMapping(models.Model):
    _name = 'exogena.concepto.mapping'
    _description = 'Mapeo de Conceptos de Exógena a Contabilidad'

    name = fields.Char(string="Descripción", compute='_compute_name', store=True)
    concepto_id = fields.Many2one(
        'exogena.concepto',
        string="Concepto DIAN",
        required=True,
        ondelete='cascade'
    )
    company_id = fields.Many2one(
        'res.company', 
        string="Compañía", 
        required=True, 
        default=lambda self: self.env.company
    )
    mapping_type = fields.Selection([
        ('tag', 'Etiqueta de Cuenta'),
        ('account', 'Cuentas Contables'),
    ], string="Tipo de Mapeo", required=True, default='tag')

    account_tag_id = fields.Many2one(
        'account.account.tag',
        string="Etiqueta de Cuenta",
        help="Usar una etiqueta para agrupar dinámicamente varias cuentas contables."
    )
    account_ids = fields.Many2many(
        'account.account',
        string="Cuentas Contables",
        help="Seleccionar cuentas específicas para este mapeo."
    )

    column_dest = fields.Selection([
        ('pago_deducible', 'Pago o Abono en Cuenta Deducible'),
        ('pago_no_deducible', 'Pago o Abono en Cuenta NO Deducible'),
        ('iva_mayor_valor_costo_deducible', 'IVA Mayor Valor del Costo o Gasto Deducible'),
        ('iva_mayor_valor_costo_no_deducible', 'IVA Mayor Valor del Costo o Gasto NO Deducible'),
        ('retencion_renta', 'Retención de Renta Practicada'),
        ('retencion_renta_asumida', 'Retención de Renta Asumida'),
        ('retencion_iva_regimen_comun', 'Retención de IVA a Régimen Común'),
        ('retencion_iva_practicada_no_domiciliado', 'Retención de IVA practicada a no domiciliados'),
    ], string="Columna de Destino (Formato 1001)", required=True)

    move_type = fields.Selection([
        ('debit', 'Débitos'),
        ('credit', 'Créditos'),
    ], string="Tipo de Movimiento a Sumar", required=True)
    
    @api.constrains('mapping_type', 'account_tag_id', 'account_ids')
    def _check_mapping_source(self):
        for record in self:
            if record.mapping_type == 'tag' and not record.account_tag_id:
                raise ValidationError("Debe seleccionar una Etiqueta de Cuenta para el tipo de mapeo 'Etiqueta'.")
            if record.mapping_type == 'account' and not record.account_ids:
                raise ValidationError("Debe seleccionar al menos una Cuenta Contable para el tipo de mapeo 'Cuentas'.")

    @api.depends('concepto_id', 'column_dest', 'mapping_type', 'account_tag_id', 'account_ids')
    def _compute_name(self):
        for rec in self:
            col_name = dict(rec._fields['column_dest'].selection).get(rec.column_dest)
            if rec.mapping_type == 'tag' and rec.account_tag_id:
                source_name = rec.account_tag_id.name
            elif rec.mapping_type == 'account':
                source_name = f"{len(rec.account_ids)} cuenta(s)"
            else:
                source_name = "N/A"
            rec.name = f"Concepto {rec.concepto_id.code} -> {col_name} ({source_name})"