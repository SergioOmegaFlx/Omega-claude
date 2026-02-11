# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ExogenaReportLineF1001(models.Model):
    _name = 'exogena.report.line.f1001'
    _description = 'Línea de Reporte de Exógena - Formato 1001'
    _order = 'concepto_id, partner_id'

    # ... (todos los campos y el método _compute_partner_data se mantienen igual) ...
    report_id = fields.Many2one('exogena.report', string="Reporte Padre", required=True, ondelete='cascade')
    company_id = fields.Many2one(related='report_id.company_id', store=True)
    concepto_id = fields.Many2one('exogena.concepto', string="Concepto")
    partner_id = fields.Many2one('res.partner', string="Tercero")
    doc_type = fields.Selection(
        string="Tipo Doc.",
        selection=[
            ('rut', 'NIT'),
            ('cedula', 'Cédula de Ciudadanía'),
            ('pasaporte', 'Pasaporte'),
            ('tarjeta_identidad', 'Tarjeta de Identidad'),
            ('cedula_extranjeria', 'Cédula de Extranjería'),
            ('nit_otro_pais', 'NIT de otro país'),
            ('registro_civil', 'Registro Civil'),
        ],
        compute='_compute_partner_data',
        store=True
    )
    vat = fields.Char(string="Identificación", compute='_compute_partner_data', store=True)
    dv = fields.Char(string="DV", compute='_compute_dv', store=True)
    partner_name_1 = fields.Char(string="Primer Apellido", compute='_compute_partner_data', store=True)
    partner_name_2 = fields.Char(string="Segundo Apellido", compute='_compute_partner_data', store=True)
    partner_firstname = fields.Char(string="Primer Nombre", compute='_compute_partner_data', store=True)
    partner_othername = fields.Char(string="Otros Nombres", compute='_compute_partner_data', store=True)
    razon_social = fields.Char(string="Razón Social", compute='_compute_partner_data', store=True)
    partner_country_code = fields.Char(string="País", compute='_compute_partner_data', store=True)
    pago_deducible = fields.Float(string="Pagos Deducibles")
    pago_no_deducible = fields.Float(string="Pagos NO Deducibles")
    iva_mayor_valor_costo_deducible = fields.Float(string="IVA Mayor Valor Deducible")
    iva_mayor_valor_costo_no_deducible = fields.Float(string="IVA Mayor Valor NO Deducible")
    retencion_renta = fields.Float(string="Ret. Renta Practicada")
    retencion_renta_asumida = fields.Float(string="Ret. Renta Asumida")
    retencion_iva_regimen_comun = fields.Float(string="Ret. IVA a Régimen Común")
    retencion_iva_practicada_no_domiciliado = fields.Float(string="Ret. IVA a no Domiciliados")

    @api.depends('partner_id')
    def _compute_partner_data(self):
        for line in self:
            if line.partner_id:
                partner = line.partner_id
                line.doc_type = getattr(partner, 'l10n_co_document_type', False)
                line.vat = getattr(partner, 'vat', False)
                line.partner_name_1 = getattr(partner, 'l10n_co_name_1', False)
                line.partner_name_2 = getattr(partner, 'l10n_co_name_2', False)
                line.partner_firstname = getattr(partner, 'l10n_co_firstname', False)
                line.partner_othername = getattr(partner, 'l10n_co_othername', False)
                line.razon_social = partner.name if partner.is_company else ''
                line.partner_country_code = getattr(partner.country_id, 'code', False)
            else:
                line.doc_type = False
                line.vat = False
                line.partner_name_1 = False
                line.partner_name_2 = False
                line.partner_firstname = False
                line.partner_othername = False
                line.razon_social = False
                line.partner_country_code = False

    # --- MÉTODO CORREGIDO ---
    @api.depends('vat')
    def _compute_dv(self):
        """
        Calcula el dígito de verificación de un NIT para Colombia.
        Esta función ahora es autocontenida y no depende de l10n_co.
        """
        factors = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]
        for line in self:
            if not line.vat or not line.vat.isdigit():
                line.dv = ''
                continue

            vat_str = line.vat.rjust(15, '0')
            total = sum(int(vat_str[i]) * factors[i] for i in range(15))
            remainder = total % 11
            
            if remainder < 2:
                line.dv = str(remainder)
            else:
                line.dv = str(11 - remainder)