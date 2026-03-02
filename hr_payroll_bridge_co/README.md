# hr_payroll_bridge_co
Puente que convierte líneas de `hr.overtime` y `hr.recargo` aprobadas en `hr.work.entry`
para que las reglas del partner (sos_l10n_co_nomina) las consuman.

- Hook: `hr.attendance.action_second_approve`
- Idempotente: borra WEs previos en borrador y recrea; bloquea si ya están validados.
- Traza: guarda `work_entry_id` en cada línea de overtime/recargo.