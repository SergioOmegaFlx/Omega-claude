# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model_create_multi
    def create(self, vals):
        structures = super().create(vals)
        to_unlink = self.env["hr.salary.rule"]
        for struct in structures:
            if struct.country_id.code != "CO":
                continue
            to_unlink += struct.rule_ids.filtered(lambda r: r.code in ["ATTACH_SALARY", "ASSIG_SALARY", "DEDUCTION", "REIMBURSEMENT", "CHILD_SUPPORT", "BASIC", "GROSS","NET"])
        to_unlink.unlink()
        return structures