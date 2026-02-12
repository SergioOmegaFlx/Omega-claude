# l10n_co_dian_1001/reports/dian_1001_report.py
from odoo import models


class Dian1001Report(models.AbstractModel):
    _name = "report.l10n_co_dian_1001.dian_1001_report"
    _description = "DIAN Exógena Formato 1001 - Report"

    def _get_report_values(self, docids, data=None):
        wizards = self.env["dian.report.wizard"].browse(docids)
        wizard = wizards[:1]
        if not wizard:
            return {}

        lines = wizard.get_report_lines()

        return {
            "doc_ids": wizard.ids,
            "doc_model": "dian.report.wizard",
            "docs": wizard,
            "lines": lines,
        }
