from odoo import fields, models

class Employee(models.Model):
    _inherit = 'hr.employee'

    intereses_prestamo_vivienda = fields.Monetary(
        string="Intereses Préstamo Vivienda",
        help="Intereses anuales pagados por préstamos de vivienda."
    )
    derecho_a_dependientes = fields.Selection(
        selection=[('SI', 'Sí'), ('NO', 'No')],
        string="Derecho a Dependientes",
        help="Indica si el empleado tiene derecho a la deducción por dependientes."
    )
    pagos_salud_prepagada = fields.Monetary(
        string="Pagos Salud Prepagada",
        help="Pagos anuales por salud prepagada, plan complementario o seguros de salud."
    )
    aportes_voluntarios_pensiones = fields.Monetary(
        string="Aportes Voluntarios Pensiones Obligatorias",
        help="Aportes voluntarios anuales a fondos de pensiones obligatorias."
    )
    aportes_voluntarios_pensiones_adicional = fields.Monetary(
        string="Aportes Voluntarios Pensiones Voluntarias",
        help="Aportes voluntarios anuales a fondos de pensiones voluntarias."
    )
    aportes_afc_avc = fields.Monetary(
        string="Aportes a Cuentas AFC/AVC",
        help="Aportes anuales a cuentas AFC o AVC."
    )
    indemnizacion_accidente_trabajo_enfermedad = fields.Monetary(
        string="Indemnización Accidente o Enfermedad",
        help="Indemnizaciones anuales por accidentes de trabajo o enfermedad."
    )
    indemnizacion_proteccion_maternidad = fields.Monetary(
        string="Indemnización Protección Maternidad",
        help="Indemnizaciones anuales por protección a la maternidad."
    )
    gasto_entierro_trabajador = fields.Monetary(
        string="Gastos de Entierro del Trabajador",
        help="Gastos de entierro anuales del trabajador."
    )
    otras_rentas_exentas = fields.Monetary(
        string="Otras Rentas Exentas",
        help="Otras rentas exentas anuales que el empleado puede deducir."
    )
