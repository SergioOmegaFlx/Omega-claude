/** @odoo-module */

// CORRECCIÓN: Se cambia la ruta de importación y el nombre del componente
// La ruta ahora apunta a la nueva ubicación en Odoo 18.
// El componente 'MyAttendances' ahora se llama 'AttendanceSystray'.
import { AttendanceSystray } from "@hr_attendance/components/attendance_systray/attendance_systray";
import { patch } from "@web/core/utils/patch";

// CORRECCIÓN: Se actualiza el prototipo que se va a "parchar".
patch(AttendanceSystray.prototype, "hr_overtime_co_extended.systray", {
    update(attendance) {
        // La lógica interna de tu método se mantiene, ya que es correcta.
        this._super(...arguments);
        const systrayElement = this.el;
        if (!systrayElement) {
            return;
        }
        systrayElement.classList.toggle("checked_in", !attendance.check_out);
    },
});