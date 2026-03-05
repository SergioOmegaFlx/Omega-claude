# -*- coding: utf-8 -*-
from odoo import models, fields

class HrContract(models.Model):
    _inherit = 'hr.contract'

    daily_hours = fields.Float(
        string="Horas Diarias (Referencia)",
        default=8.0,
        help="Número de horas de referencia por día. El cálculo de horas extras se basa en las horas semanales."
    )
    weekly_hours = fields.Float(
        string="Horas Semanales por Contrato",
        default=44.0,  # AJUSTADO: Límite legal según la reforma 2025
        help="Número total de horas que el empleado debe trabajar por semana antes de que se generen horas extras."
    )