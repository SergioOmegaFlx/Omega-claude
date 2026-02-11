# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date

class ExogenaGenerationWizard(models.TransientModel):
    _name = 'exogena.generation.wizard'
    _description = 'Asistente para Generación de Información Exógena'

    @api.model
    def _default_year(self):
        return date.today().year

    year = fields.Integer(
        string="Año Fiscal",
        required=True,
        default=_default_year
    )
    date_from = fields.Date(string="Desde", compute='_compute_dates', readonly=True)
    date_to = fields.Date(string="Hasta", compute='_compute_dates', readonly=True)

    format_id = fields.Many2one(
        'exogena.format',
        string="Formato a Generar",
        required=True,
        domain="[('active', '=', True)]"
    )
    uvt_value = fields.Float(string="Valor UVT del Año Fiscal", required=True, digits=(16, 2))
    company_id = fields.Many2one('res.company', string="Compañía", required=True, default=lambda self: self.env.company)

    @api.depends('year')
    def _compute_dates(self):
        for wizard in self:
            if wizard.year:
                wizard.date_from = date(wizard.year, 1, 1)
                wizard.date_to = date(wizard.year, 12, 31)
            else:
                wizard.date_from = False
                wizard.date_to = False

    @api.onchange('year')
    def _onchange_year_set_uvt(self):
        if self.year:
            uvt_record = self.env['exogena.uvt'].search([
                ('year', '=', self.year),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            if uvt_record:
                self.uvt_value = uvt_record.value
            else:
                self.uvt_value = 0
                return {'warning': {
                    'title': "Valor UVT no encontrado",
                    'message': f"No se encontró un valor de UVT configurado para el año {self.year}. Por favor, configúrelo en el menú de Exógena > Configuración > Valores UVT."
                }}
        else:
            self.uvt_value = 0

    def action_generate_report(self):
        self.ensure_one()
        if self.uvt_value <= 0:
            raise UserError("El valor de la UVT debe ser mayor que cero.")

        report = self.env['exogena.report'].create({
            'name': f"{self.format_id.code} - {self.year}",
            'year': self.year,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'format_id': self.format_id.id,
            'company_id': self.company_id.id,
            'state': 'processing',
        })

        # --- LLAMADA DIRECTA A LA LÓGICA DE CÁLCULO ---
        # En una implementación final, esto se haría con un "background job"
        # report.with_delay()._generate_f1001_data(self.uvt_value)
        if report.format_id.code == '1001':
            report._generate_f1001_data(self.uvt_value)
        
        report.state = 'done'
        # --- Fin de la llamada ---

        return {
            'type': 'ir.actions.act_window',
            'name': 'Reporte Generado',
            'res_model': 'exogena.report',
            'view_mode': 'form',
            'res_id': report.id,
            'target': 'current',
        }