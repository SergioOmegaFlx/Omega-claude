# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta, date
import pytz
import holidays

_logger = logging.getLogger(__name__)

class HrAttendance(models.Model):
    """
    Se heredan los mixins de mail directamente aquí para gestionar el flujo
    de notificaciones y actividades relacionadas con las aprobaciones.
    """
    _name = 'hr.attendance'
    _inherit = ['hr.attendance', 'mail.thread', 'mail.activity.mixin']

    # --- CAMPOS (Sin cambios) ---
    overtime_ids = fields.One2many('hr.overtime', 'attendance_id', string='Horas Extras')
    recargo_ids = fields.One2many('hr.recargo', 'attendance_id', string='Recargos')
    total_overtime_hours = fields.Float(string="Total Horas Extras", compute='_compute_totals', store=True)
    total_overtime_amount = fields.Float(string="Valor Horas Extras", compute='_compute_totals', store=True)
    total_recargo_hours = fields.Float(string="Total Horas Recargo", compute='_compute_totals', store=True)
    total_recargo_amount = fields.Float(string="Valor Recargos", compute='_compute_totals', store=True)
    cumulative_weekly_hours = fields.Float(string="Horas Acumuladas en la Semana", compute='_compute_cumulative_weekly_hours')
    current_total_hours = fields.Float(string="Horas Totales de la Semana", compute='_compute_current_total_hours')
    state = fields.Selection([
        ('to_approve_1', 'Esperando Aprobación 1'),
        ('to_approve_2', 'Esperando Aprobación 2'),
        ('approved', 'Aprobado'),
        ('paid', 'Pagado'),
        ('rejected', 'Rechazado'),
    ], string='Estado', default='approved', readonly=True, copy=False, tracking=True)
    is_current_user_supervisor = fields.Boolean(compute='_compute_is_current_user_approver')
    is_current_user_manager = fields.Boolean(compute='_compute_is_current_user_approver')
    is_current_user_accountant = fields.Boolean(compute='_compute_is_current_user_approver')

    # --- MÉTODOS COMPUTE (Sin cambios) ---
    @api.depends('cumulative_weekly_hours', 'worked_hours')
    def _compute_current_total_hours(self):
        for att in self:
            effective_current_day = max(0, att.worked_hours - 1.0)
            att.current_total_hours = att.cumulative_weekly_hours + effective_current_day

    def _compute_is_current_user_approver(self):
        for att in self:
            att.is_current_user_supervisor = self.env.user == att.employee_id.overtime_supervisor_id
            att.is_current_user_manager = self.env.user == att.employee_id.overtime_manager_id
            att.is_current_user_accountant = self.env.user.has_group('account.group_account_user')

    @api.depends('overtime_ids.duration', 'overtime_ids.amount', 'recargo_ids.duration', 'recargo_ids.amount')
    def _compute_totals(self):
        for att in self:
            att.total_overtime_hours = sum(att.overtime_ids.mapped('duration'))
            att.total_overtime_amount = sum(att.overtime_ids.mapped('amount'))
            att.total_recargo_hours = sum(att.recargo_ids.mapped('duration'))
            att.total_recargo_amount = sum(att.recargo_ids.mapped('amount'))

    @api.depends('employee_id', 'check_in')
    def _compute_cumulative_weekly_hours(self):
        for att in self:
            if not att.employee_id or not att.check_in:
                att.cumulative_weekly_hours = 0.0
                continue
            current_date = att.check_in.date()
            start_of_week = current_date - timedelta(days=current_date.weekday())
            previous_attendances = self.search([
                ('employee_id', '=', att.employee_id.id),
                ('check_in', '>=', start_of_week),
                ('check_in', '<', current_date),
                ('check_out', '!=', False)
            ])
            cumulative_hours = 0.0
            LUNCH_HOURS = 1.0
            # --- NUEVO: Límite de horas diarias ---
            DAILY_HOURS_LIMIT = 10.0
            for prev_att in previous_attendances:
                worked_duration = (prev_att.check_out - prev_att.check_in).total_seconds() / 3600.0
                effective_hours_this_day = max(0, worked_duration - LUNCH_HOURS)
                # Acumulamos solo las horas ordinarias para el cálculo semanal
                ordinary_hours = min(effective_hours_this_day, DAILY_HOURS_LIMIT)
                cumulative_hours += ordinary_hours
            att.cumulative_weekly_hours = cumulative_hours
    
    # --- LÓGICA PRINCIPAL Y NOTIFICACIONES (MODIFICADA) ---
    def _recompute_weekly_overtime(self, employee, any_date_in_week):
        contract = employee.contract_id
        if not contract:
            return

        # --- LÓGICA DE LÍMITE SEMANAL (AJUSTADA A 2025 ) ---
        limit = 44.0 # Límite para 2025
        if any_date_in_week < date(2024, 7, 15):
            limit = 47.0
        elif any_date_in_week < date(2025, 7, 15):
            limit = 46.0
        
        weekly_hours_limit = limit
        # --- NUEVO: Límite diario ---
        DAILY_HOURS_LIMIT = 10.0

        start_of_week = any_date_in_week - timedelta(days=any_date_in_week.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        weekly_attendances = self.search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', start_of_week),
            ('check_in', '<=', end_of_week),
            ('check_out', '!=', False)
        ], order='check_in asc')
        
        attendances_to_reset = weekly_attendances.filtered(lambda att: att.state != 'paid')
        
        if not self.env.context.get('recomputing'):
            attendances_to_reset.with_context(recomputing=True).write({'state': 'approved'})
        
        attendances_to_reset.overtime_ids.sudo().unlink()
        attendances_to_reset.recargo_ids.sudo().unlink()

        cumulative_hours = 0.0
        LUNCH_HOURS = 1.0

        for att in attendances_to_reset:
            worked_duration = (att.check_out - att.check_in).total_seconds() / 3600.0
            effective_hours_this_day = max(0, worked_duration - LUNCH_HOURS)
            check_in_aware = att._get_tz_aware_datetime(att.check_in)
            check_out_aware = att._get_tz_aware_datetime(att.check_out)
            
            # 1. Cálculo de Recargos (esto no cambia)
            if not self.env.context.get('recomputing'):
                att._consolidate_and_create('hr.recargo', check_in_aware, check_out_aware, att)
            
            # --- NUEVA LÓGICA HÍBRIDA ---
            
            # 2. Calcular Horas Extras DIARIAS
            daily_overtime_hours = 0
            if effective_hours_this_day > DAILY_HOURS_LIMIT:
                daily_overtime_hours = effective_hours_this_day - DAILY_HOURS_LIMIT
                
                # Hora de inicio de las horas extras diarias
                overtime_start_daily_aware = check_in_aware + timedelta(hours=DAILY_HOURS_LIMIT + LUNCH_HOURS)
                att._consolidate_and_create('hr.overtime', overtime_start_daily_aware, check_out_aware, att)
            
            # 3. Calcular Horas Extras SEMANALES
            # Las horas que se suman al acumulado semanal son solo las ordinarias de ese día
            ordinary_hours_this_day = effective_hours_this_day - daily_overtime_hours
            
            hours_before_this_day = cumulative_hours
            cumulative_hours += ordinary_hours_this_day
            
            weekly_overtime_hours = 0
            if hours_before_this_day >= weekly_hours_limit:
                weekly_overtime_hours = ordinary_hours_this_day
            elif cumulative_hours > weekly_hours_limit:
                weekly_overtime_hours = cumulative_hours - weekly_hours_limit
            
            if weekly_overtime_hours > 0:
                # Hora de inicio de las horas extras semanales
                ordinary_hours_before_weekly_overtime = ordinary_hours_this_day - weekly_overtime_hours
                overtime_start_weekly_aware = check_in_aware + timedelta(hours=ordinary_hours_before_weekly_overtime + LUNCH_HOURS)
                
                # Asegurarnos de no procesar el mismo tiempo que ya fue extra diaria
                # El final de las extras semanales es el inicio de las extras diarias
                overtime_end_weekly_aware = check_out_aware - timedelta(hours=daily_overtime_hours)

                att._consolidate_and_create('hr.overtime', overtime_start_weekly_aware, overtime_end_weekly_aware, att)

        weekly_attendances.invalidate_recordset()

        if not self.env.context.get('recomputing'):
            for att in attendances_to_reset:
                att._clear_approval_activities()
                if att.total_overtime_hours > 0:
                    att.write({'state': 'to_approve_1'})
                    att._schedule_approval_activity(approver_field='overtime_supervisor_id')
                else:
                    att.write({'state': 'approved'})
    
    # --- MÉTODOS DE ACTIVIDADES Y ACCIONES (Sin cambios) ---
    def _schedule_approval_activity(self, approver_field=None):
        self.ensure_one()
        activity_type_id = self.env.ref('hr_overtime_co_extended.mail_activity_type_overtime_approval').id
        approver = self.employee_id[approver_field] if approver_field else self.env.user
        if not approver:
            _logger.warning(f"No activity scheduled for attendance {self.id}: approver not found on field '{approver_field}'.")
            return
        self.activity_schedule(
            activity_type_id=activity_type_id,
            summary=f"Revisar Horas Extras para {self.employee_id.name}",
            note=f"Por favor, apruebe o rechace el registro de asistencia del {self.check_in.date()} que contiene horas extras.",
            user_id=approver.id
        )

    def _clear_approval_activities(self):
        self.activity_unlink(['hr_overtime_co_extended.mail_activity_type_overtime_approval'])

    def action_first_approve(self):
        self.ensure_one()
        if not self.env.user == self.employee_id.overtime_supervisor_id:
            raise UserError("No tienes permiso para realizar esta aprobación.")
        self._clear_approval_activities()
        self.write({'state': 'to_approve_2'})
        self._schedule_approval_activity(approver_field='overtime_manager_id')

    def action_second_approve(self):
        self.ensure_one()
        if not self.env.user == self.employee_id.overtime_manager_id:
            raise UserError("No tienes permiso para realizar esta aprobación.")
        self._clear_approval_activities()
        self.write({'state': 'approved'})

    def action_reject(self):
        for rec in self:
            is_supervisor = self.env.user == rec.employee_id.overtime_supervisor_id
            is_manager = self.env.user == rec.employee_id.overtime_manager_id
            if not (is_supervisor or is_manager):
                raise UserError("No tienes permiso para rechazar este registro.")
            rec._clear_approval_activities()
            rec.write({'state': 'rejected'})

    def action_mark_as_paid(self):
        self.ensure_one()
        if not self.env.user.has_group('account.group_account_user'):
            raise UserError("Solo los usuarios del equipo de contabilidad pueden marcar el registro como pagado.")
        self._clear_approval_activities()
        self.write({'state': 'paid'})
    
    @api.model_create_multi
    def create(self, vals_list):
        records = super(HrAttendance, self).create(vals_list)
        for record in records.filtered(lambda r: r.check_in and r.check_out):
            self.env['hr.attendance']._recompute_weekly_overtime(record.employee_id, record.check_in.date())
        return records

    def write(self, vals):
        res = super(HrAttendance, self).write(vals)
        if 'check_in' in vals or 'check_out' in vals:
            for record in self.filtered(lambda r: r.check_in and r.check_out):
                # --- MODIFICADO: Se elimina la condición de estado para permitir recálculo ---
                self.env['hr.attendance']._recompute_weekly_overtime(record.employee_id, record.check_in.date())
        return res
        
    # --- MÉTODOS HELPER (Sin cambios) ---
    def _consolidate_and_create(self, model_name, start_dt, end_dt, attendance_record):
        if not (start_dt and end_dt and start_dt < end_dt): return
        common_vals = {'employee_id': attendance_record.employee_id.id, 'attendance_id': attendance_record.id}
        types_dict = {}
        type_func = None
        if model_name == 'hr.overtime': types_dict = {t.code: t for t in self.env['hr.overtime.type'].search([])}; type_func = self._get_overtime_type_for_datetime
        else: types_dict = {t.code: t for t in self.env['hr.recargo.type'].search([])}; type_func = self._get_recargo_types_for_datetime
        records_to_create = []
        current_dt = start_dt
        while current_dt < end_dt:
            block_start_dt = current_dt
            current_types = type_func(current_dt, types_dict)
            next_dt = current_dt + timedelta(minutes=1)
            while next_dt < end_dt and type_func(next_dt, types_dict) == current_types: next_dt += timedelta(minutes=1)
            block_end_dt = next_dt
            if current_types:
                type_list = current_types if isinstance(current_types, list) else [current_types]
                for type_id in type_list:
                    if not type_id: continue
                    vals = {**common_vals, 'type_id': type_id.id, 'date_start': self._get_naive_utc_datetime(block_start_dt), 'date_end': self._get_naive_utc_datetime(block_end_dt)}
                    records_to_create.append(vals)
            current_dt = block_end_dt
        if records_to_create: self.env[model_name].sudo().create(records_to_create)

    def _get_tz_aware_datetime(self, naive_dt):
        if not naive_dt: return None
        tz = pytz.timezone(self.employee_id.tz or 'America/Bogota')
        return pytz.utc.localize(naive_dt).astimezone(tz)

    def _get_naive_utc_datetime(self, aware_dt):
        if not aware_dt: return None
        return aware_dt.astimezone(pytz.utc).replace(tzinfo=None)

    def _is_holiday_or_sunday(self, date_aware):
        if date_aware.weekday() == 6:
            return True
        co_holidays = holidays.Colombia(years=date_aware.year)
        return date_aware.date() in co_holidays

    def _get_overtime_type_for_datetime(self, dt_aware, overtime_types):
        is_night = not (6 <= dt_aware.hour < 19)
        is_sunday_holiday = self._is_holiday_or_sunday(dt_aware)
        code = 'HEND' if is_sunday_holiday and is_night else 'HEDD' if is_sunday_holiday and not is_night else 'HEN' if not is_sunday_holiday and is_night else 'HED'
        return overtime_types.get(code)
        
    def _get_recargo_types_for_datetime(self, dt_aware, recargo_types):
        applicable_recargos = []
        if not (6 <= dt_aware.hour < 19) and recargo_types.get('RN'):
            applicable_recargos.append(recargo_types['RN'])
        
        co_holidays = holidays.Colombia(years=dt_aware.year)
        is_holiday = dt_aware.date() in co_holidays
        is_sunday = dt_aware.weekday() == 6

        if is_holiday and recargo_types.get('RF'):
            applicable_recargos.append(recargo_types['RF'])
        elif is_sunday and recargo_types.get('RD'):
            applicable_recargos.append(recargo_types['RD'])

        return applicable_recargos

    def action_reset_to_draft(self):
        employee = self.employee_id
        check_in_date = self.check_in.date()
        if not self.env.user == employee.overtime_manager_id: raise UserError("Solo el Gerente de Horas Extras asignado puede forzar un recálculo.")
        self.state = 'to_approve_1' 
        self.env['hr.attendance'].with_context(resetting_attendances=True)._recompute_weekly_overtime(employee, check_in_date)