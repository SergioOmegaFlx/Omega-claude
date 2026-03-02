# hr_payroll_bridge_co/models/hr_attendance.py
from odoo import models, fields, _
from odoo.exceptions import UserError


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    # Mapeo de tus códigos → códigos del partner
    CODE_MAP = {
        # Horas extra
        "HED": "HED",
        "HEN": "HEN",
        "HEDD": "HEDDF",
        "HEND": "HENDF",
        # Recargos
        "RN": "RN",
        "RD": "RDF",
        "RF": "RDF",
        # Combinado (si aplica en tu módulo)
        "RND": "RNDF",
    }

    work_entry_count = fields.Integer(
        string="Work Entries",
        compute="_compute_work_entry_count",
        readonly=True,
    )

    # --- Hook aprobación 2 (Gerente) ---
    def action_second_approve(self):
        res = super().action_second_approve()
        approved = self.filtered(lambda a: a.state == "approved")
        if approved:
            approved._export_attendance_to_work_entries()
        return res

    # --- Exportar líneas aprobadas a hr.work.entry ---
    def _export_attendance_to_work_entries(self):
        WorkEntryType = self.env["hr.work.entry.type"]
        HrOvertime = self.env["hr.overtime"]
        HrRecargo = self.env["hr.recargo"]

        def _cleanup_previous_wes(batch):
            """Borra WEs previos si están en estado seguro y limpia el m2o."""
            if not batch:
                return
            wes = batch.mapped("work_entry_id")
            if not wes:
                return
            unsafe = wes.filtered(lambda we: getattr(we, "state", "draft") not in ("draft", "generated"))
            if unsafe:
                raise UserError(_(
                    "No se puede regenerar porque existen Work Entries validados/bloqueados:\n- %s"
                ) % ("\n- ".join(unsafe.mapped("display_name"))))
            wes.unlink()
            batch.write({"work_entry_id": False})

        def _create_we_for_line(att, line):
            """Crea un Work Entry para una línea de overtime/recargo, evitando solapes."""
            emp = att.employee_id
            contract = emp.contract_id
            if not contract:
                raise UserError(_("No se encontró contrato activo para %s.") % emp.name)

            if not line.duration or line.duration <= 0:
                return None
            if not line.date_start or not getattr(line, "date_end", False):
                raise UserError(_("Faltan fechas en la línea %s.") % (line.display_name,))
            if not line.type_id or not line.type_id.code:
                raise UserError(_("La línea %s no tiene tipo/código.") % (line.display_name,))

            src_code = line.type_id.code.strip()
            dst_code = self.CODE_MAP.get(src_code, src_code)
            wet = WorkEntryType.search([("code", "=", dst_code)], limit=1)
            if not wet:
                raise UserError(_("No existe hr.work.entry.type con código '%s' (desde '%s').") % (dst_code, src_code))

            # Evitar superposición con otras entradas del empleado
            overlaps = self.env["hr.work.entry"].search([
                ("employee_id", "=", emp.id),
                ("date_start", "<", line.date_end),
                ("date_stop", ">", line.date_start),
            ])

            new_start = line.date_start
            if overlaps:
                latest_end = max(overlaps.mapped("date_stop"))
                if latest_end >= line.date_end:
                    # La línea quedaría completamente cubierta: no crear WE
                    return None
                if latest_end > line.date_start:
                    new_start = latest_end  # recortar inicio al final del último WE

            # Si tras recortar no queda rango, no crear
            if new_start >= line.date_end:
                return None

            we = self.env["hr.work.entry"].create({
                "name": "%s - %s" % (wet.name, emp.name),
                "employee_id": emp.id,
                "contract_id": contract.id,
                "work_entry_type_id": wet.id,
                "date_start": new_start,
                "date_stop": line.date_end,
            })
            line.work_entry_id = we.id
            return we

        # --- Iterar asistencias y crear WEs ---
        for att in self:
            overtime_lines = HrOvertime.search([("attendance_id", "=", att.id)])
            recargo_lines = HrRecargo.search([("attendance_id", "=", att.id)])

            if not overtime_lines and not recargo_lines:
                continue

            _cleanup_previous_wes(overtime_lines)
            _cleanup_previous_wes(recargo_lines)

            for line in overtime_lines:
                _create_we_for_line(att, line)
            for line in recargo_lines:
                _create_we_for_line(att, line)

    # --- Contador para Smart Button ---
    def _compute_work_entry_count(self):
        WorkEntry = self.env["hr.work.entry"]
        HrOvertime = self.env["hr.overtime"]
        HrRecargo = self.env["hr.recargo"]

        for att in self:
            we_ids = []
            ot_lines = HrOvertime.search([("attendance_id", "=", att.id)])
            if ot_lines:
                we_ids += ot_lines.mapped("work_entry_id").ids
            rc_lines = HrRecargo.search([("attendance_id", "=", att.id)])
            if rc_lines:
                we_ids += rc_lines.mapped("work_entry_id").ids
            we_ids = list({wid for wid in we_ids if wid})
            att.work_entry_count = WorkEntry.search_count([("id", "in", we_ids)])

    # --- Acción del Smart Button ---
    def action_open_work_entries(self):
        self.ensure_one()
        HrOvertime = self.env["hr.overtime"]
        HrRecargo = self.env["hr.recargo"]

        we_ids = []
        ot_lines = HrOvertime.search([("attendance_id", "=", self.id)])
        if ot_lines:
            we_ids += ot_lines.mapped("work_entry_id").ids
        rc_lines = HrRecargo.search([("attendance_id", "=", self.id)])
        if rc_lines:
            we_ids += rc_lines.mapped("work_entry_id").ids
        we_ids = list({wid for wid in we_ids if wid})

        return {
            "type": "ir.actions.act_window",
            "name": _("Work Entries"),
            "res_model": "hr.work.entry",
            "view_mode": "list,form",  # Odoo 18
            "domain": [("id", "in", we_ids)] if we_ids else [("id", "=", 0)],
            "target": "current",
            "context": {"default_employee_id": self.employee_id.id},
        }
