from odoo import models, fields

class HrOvertime(models.Model):
    _inherit = "hr.overtime"

    work_entry_id = fields.Many2one(
        "hr.work.entry",
        string="Work Entry",
        readonly=True,
        copy=False,
        index=True,
    )
