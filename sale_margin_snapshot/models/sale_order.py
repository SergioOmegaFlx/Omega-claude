from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    x_studio_plan_piloto_costo = fields.Boolean(
        string='Plan piloto de costo'
    )
