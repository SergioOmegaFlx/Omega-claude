# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Campos de aprobadores
    overtime_supervisor_id = fields.Many2one(
        'res.users',
        string='Supervisor de Horas Extras',
        help='Este usuario será responsable de la primera aprobación de las asistencias.'
    )
    overtime_manager_id = fields.Many2one(
        'res.users',
        string='Gerente de Horas Extras',
        help='Este usuario será responsable de la segunda y final aprobación de las asistencias.'
    )

    # --- CORRECCIÓN FINAL ---
    # Se elimina el decorador @api.model para resolver el TypeError.
    # El método ahora es un método de instancia estándar, que es lo que
    # la llamada desde el JavaScript estaba esperando.
    def get_user_attendance_state(self):
        """
        Devuelve el estado de asistencia del empleado actual para el UI.
        """
        # Aunque es un método de instancia, no usamos 'self' directamente.
        # Obtenemos el empleado a partir del usuario que ha iniciado sesión.
        employee = self.env.user.employee_id
        if not employee:
            return {'state': 'no_employee'}

        open_attendance = self.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1, order='check_in desc')

        if open_attendance:
            return {
                'state': 'checked_in',
                'check_in_time': open_attendance.check_in,
                'employee_name': employee.name,
            }
        else:
            return {
                'state': 'checked_out',
                'employee_name': employee.name,
            }

    def _cron_notify_open_attendances(self):
        """
        Busca empleados con sesiones de asistencia abiertas y les envía un mensaje por chat.
        """
        open_attendances = self.env['hr.attendance'].search([('check_out', '=', False)])
        odoobot_partner = self.env.ref('base.partner_root')

        for attendance in open_attendances:
            employee = attendance.employee_id
            partner = employee.user_id.partner_id
            if partner:
                partner.message_post(
                    body="Detectamos que tu sesión de asistencia sigue activa. Si ya finalizaste, por favor, no olvides registrar tu salida.",
                    author_id=odoobot_partner.id,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )