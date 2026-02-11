from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    x_studio_usd_cost = fields.Float(
        string='USD Cost',
        store=True,
        readonly=True
    )

    # 🔹 Tabla de costos (la misma que ya usas)
    def _get_usd_cost(self):
        self.ensure_one()

        COSTOS_PILOTO = {
            31294: 225.742, 31296: 259.312, 31295: 259.312,
            31297: 257.18, 31241: 245.15, 31298: 275.66,
            31299: 354.44, 30575: 70.0, 30576: 70.0,
            30531: 0.0, 28936: 60.0,
        }

        if not self.product_id:
            return 0.0

        template_id = self.product_id.product_tmpl_id.id

        if self.order_id.x_studio_plan_piloto_costo and template_id in COSTOS_PILOTO:
            return COSTOS_PILOTO[template_id]

        return self.product_id.x_studio_usd_cost

    # 🔹 UX (sigue funcionando igual)
    @api.onchange('product_id', 'order_id.x_studio_plan_piloto_costo')
    def _onchange_product_id_set_cost(self):
        for line in self:
            if line.order_id.state in ['draft', 'sent']:
                line.x_studio_usd_cost = line._get_usd_cost()

    # 🔹 PERSISTENCIA REAL (AQUÍ ESTÁ LA CLAVE)
    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if line.order_id.state in ['draft', 'sent']:
                line.x_studio_usd_cost = line._get_usd_cost()
        return lines

    def write(self, vals):
        # 🔒 Blindaje: nadie puede escribir este campo manualmente
        if 'x_studio_usd_cost' in vals:
            vals.pop('x_studio_usd_cost')

        res = super().write(vals)

        # 🔁 Recalcular SOLO cuando corresponde
        if any(k in vals for k in ['product_id', 'order_id']):
            for line in self:
                if line.order_id.state in ['draft', 'sent']:
                    line.x_studio_usd_cost = line._get_usd_cost()

        return res
