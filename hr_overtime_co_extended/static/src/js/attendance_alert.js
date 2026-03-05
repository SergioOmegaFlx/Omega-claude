/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState } from "@odoo/owl";

export class AttendanceAlert extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            attendance_state: 'loading',
            check_in_time: null,
            employee_name: null,
        });

        onWillStart(async () => {
            await this.fetchAttendanceState();
        });
    }

    async fetchAttendanceState() {
        try {
            const result = await this.orm.call(
                'hr.employee',
                'get_user_attendance_state',
                [[]]
            );
            
            this.state.attendance_state = result.state;
            if (result.state === 'checked_in') {
                const checkInDate = new Date(result.check_in_time + 'Z');
                this.state.check_in_time = checkInDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
            this.state.employee_name = result.employee_name;

        } catch (e) {
            console.error("Error fetching attendance state:", e);
            this.state.attendance_state = 'error';
        }
    }
}

AttendanceAlert.template = "hr_overtime_co_extended.AttendanceAlert";

// --- LÍNEA MODIFICADA PARA ORDENAR EL ÍCONO ---
// Se añade la propiedad "sequence" con un valor de 34.
// El ícono de asistencia de Odoo usa la secuencia 35, por lo que
// nuestra alerta ahora aparecerá justo antes.
AttendanceAlert.props = {};
registry.category("systray").add("hr_overtime_co_extended.AttendanceAlert", {
    Component: AttendanceAlert,
    sequence: 999,
});