from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # El campo 'nit' ya existe en Odoo como 'vat', pero podemos crear un alias 
    # o usar uno nuevo si prefieres manejarlo por separado para la PILA
    codigo_pila = fields.Char(string='Código PILA / SuperSalud')

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    codigo_pila = fields.Selection([
        ('VAC', 'Vacaciones (VAC)'),
        ('IGE', 'Incapacidad General (IGE)'),
        ('LMA', 'Licencia Maternidad/Paternidad (LMA)'),
        ('IRP', 'Accidente de Trabajo (IRP)'),
        ('SLN', 'Licencia No Remunerada (SLN)'),
        ('ALM', 'Licencia Remunerada (ALM)'),
    ], string='Código Novedad PILA')    


class HrContract(models.Model):
    _inherit = 'hr.contract'

    fecha_ultimo_pago_prima = fields.Date(string='Última Prima Pagada')
    fecha_ultimo_pago_cesantias = fields.Date(string='Últimas Cesantías Pagadas')
    fecha_ultimo_pago_vacaciones = fields.Date(string='Últimas Vacaciones Pagadas')