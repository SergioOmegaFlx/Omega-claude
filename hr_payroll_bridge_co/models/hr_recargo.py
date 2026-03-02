from odoo import models, fields

class HrRecargo(models.Model):
    _inherit = "hr.recargo"

    work_entry_id = fields.Many2one(
        "hr.work.entry",
        string="Work Entry",
        readonly=True,
        copy=False,
        index=True,
    )
