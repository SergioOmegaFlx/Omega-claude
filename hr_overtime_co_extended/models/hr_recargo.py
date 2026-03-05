# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrRecargo(models.Model):
    _name = 'hr.recargo'
    _description = 'Employee Surcharge Record (Recargo)'
    _order = 'date_start desc'

    # --- NUEVO CAMPO ---
    name = fields.Char(string='Description', compute='_compute_name', store=True, readonly=True)

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    attendance_id = fields.Many2one('hr.attendance', string='Attendance', required=True, ondelete='cascade')
    type_id = fields.Many2one('hr.recargo.type', string='Surcharge Type', required=True)
    date_start = fields.Datetime(string='Start Date', required=True)
    date_end = fields.Datetime(string='End Date', required=True)
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True, readonly=True)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True, readonly=True)

    # --- NUEVO MÉTODO ---
    @api.depends('employee_id.name', 'date_start', 'type_id.name')
    def _compute_name(self):
        for recargo in self:
            if recargo.employee_id and recargo.date_start and recargo.type_id:
                recargo.name = f"{recargo.type_id.name} for {recargo.employee_id.name} on {recargo.date_start.date()}"
            else:
                recargo.name = "New Surcharge Record"

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for recargo in self:
            if recargo.date_start and recargo.date_end:
                delta = recargo.date_end - recargo.date_start
                recargo.duration = delta.total_seconds() / 3600.0
            else:
                recargo.duration = 0.0

    @api.depends('duration', 'employee_id', 'type_id')
    def _compute_amount(self):
        for recargo in self:
            if not recargo.employee_id or not recargo.type_id or not recargo.duration:
                recargo.amount = 0.0
                continue
            
            contract = recargo.employee_id.contract_id
            if not contract or not contract.wage:
                recargo.amount = 0.0
                continue
            
            hourly_wage = contract.wage / 235.0
            surcharge_value = hourly_wage * (recargo.type_id.percent / 100.0)
            recargo.amount = recargo.duration * surcharge_value