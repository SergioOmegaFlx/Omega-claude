# -*- coding: utf-8 -*-
from odoo import models, fields, api

class HrOvertime(models.Model):
    _name = 'hr.overtime'
    _description = 'Employee Overtime Record'
    _order = 'date_start desc'

    # --- NUEVO CAMPO ---
    name = fields.Char(string='Description', compute='_compute_name', store=True, readonly=True)

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, index=True)
    attendance_id = fields.Many2one('hr.attendance', string='Attendance', required=True, ondelete='cascade')
    type_id = fields.Many2one('hr.overtime.type', string='Overtime Type', required=True)
    date_start = fields.Datetime(string='Start Date', required=True)
    date_end = fields.Datetime(string='End Date', required=True)
    duration = fields.Float(string='Duration (hours)', compute='_compute_duration', store=True, readonly=True)
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True, readonly=True)

    # --- NUEVO MÉTODO ---
    @api.depends('employee_id.name', 'date_start', 'type_id.name')
    def _compute_name(self):
        for overtime in self:
            if overtime.employee_id and overtime.date_start and overtime.type_id:
                overtime.name = f"{overtime.type_id.name} for {overtime.employee_id.name} on {overtime.date_start.date()}"
            else:
                overtime.name = "New Overtime Record"

    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for overtime in self:
            if overtime.date_start and overtime.date_end:
                delta = overtime.date_end - overtime.date_start
                overtime.duration = delta.total_seconds() / 3600.0
            else:
                overtime.duration = 0.0

    @api.depends('duration', 'employee_id', 'type_id')
    def _compute_amount(self):
        for overtime in self:
            if not overtime.employee_id or not overtime.type_id or not overtime.duration:
                overtime.amount = 0.0
                continue
            
            contract = overtime.employee_id.contract_id
            if not contract or not contract.wage:
                overtime.amount = 0.0
                continue
            
            hourly_wage = contract.wage / 220.0
            
            # --- CÁLCULO AJUSTADO PARA MOSTRAR VALOR TOTAL (BASE + RECARGO) ---
            total_hourly_rate = hourly_wage * (1 + (overtime.type_id.percent / 100.0))
            overtime.amount = overtime.duration * total_hourly_rate