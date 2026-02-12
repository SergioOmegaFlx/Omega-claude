# l10n_co_dian_1001/wizards/dian_report_wizard.py
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DianReportWizard(models.TransientModel):
    _name = "dian.report.wizard"
    _description = "DIAN Exógena Formato 1001 - Wizard"

    date_from = fields.Date(
        string="Fecha Desde",
        required=True,
    )
    date_to = fields.Date(
        string="Fecha Hasta",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    format_type = fields.Selection(
        selection=[("1001", "Formato 1001")],
        string="Formato DIAN",
        required=True,
        default="1001",
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to and wizard.date_from > wizard.date_to:
                raise UserError(_("La fecha inicial no puede ser mayor que la fecha final."))

    # -------------------------------------------------------------------------
    # MÉTODO CENTRAL: AGRUPACIÓN SQL
    # -------------------------------------------------------------------------
    def _get_grouped_data(self):
        """Devuelve una lista de dicts con la información consolidada por
        (partner_id, concept_id).

        Se usa SQL para rendimiento (evitar loops enormes en Python).
        """
        self.ensure_one()
        cr = self.env.cr

        # Solo conceptos del formato 1001
        concepts = self.env["dian.concepto.mapping"].search(
            [("format_type", "=", self.format_type)]
        )
        if not concepts:
            return []

        company_id = self.company_id.id
        date_from = self.date_from
        date_to = self.date_to
        format_type = self.format_type

        # --- 1) Base: pagos/abonos (debitos en cuentas base) ------------------
        base_query = """
            SELECT
                aml.partner_id AS partner_id,
                rel.concept_id AS concept_id,
                SUM(aml.debit) AS base_amount,
                STRING_AGG(DISTINCT aa.code, ', ') AS account_codes
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN dian_concept_base_account_rel rel
                ON rel.account_id = aml.account_id
            JOIN dian_concepto_mapping m
                ON m.id = rel.concept_id
            JOIN account_account aa
                ON aa.id = aml.account_id
            WHERE
                am.company_id = %s
                AND am.date >= %s
                AND am.date <= %s
                AND am.state = 'posted'
                AND m.format_type = %s
                AND aml.partner_id IS NOT NULL
            GROUP BY aml.partner_id, rel.concept_id
        """
        cr.execute(base_query, (company_id, date_from, date_to, format_type))
        base_rows = cr.fetchall()

        # --- 2) Retenciones: créditos en cuentas de retención -----------------
        tax_query = """
            SELECT
                aml.partner_id AS partner_id,
                rel.concept_id AS concept_id,
                SUM(aml.credit) AS tax_amount,
                STRING_AGG(DISTINCT aa.code, ', ') AS account_codes
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN dian_concept_tax_account_rel rel
                ON rel.account_id = aml.account_id
            JOIN dian_concepto_mapping m
                ON m.id = rel.concept_id
            JOIN account_account aa
                ON aa.id = aml.account_id
            WHERE
                am.company_id = %s
                AND am.date >= %s
                AND am.date <= %s
                AND am.state = 'posted'
                AND m.format_type = %s
                AND aml.partner_id IS NOT NULL
            GROUP BY aml.partner_id, rel.concept_id
        """
        cr.execute(tax_query, (company_id, date_from, date_to, format_type))
        tax_rows = cr.fetchall()

        # Índices de columnas
        # base_rows: partner_id, concept_id, base_amount, account_codes
        # tax_rows: partner_id, concept_id, tax_amount, account_codes

        # Unificar por (partner_id, concept_id)
        grouped = defaultdict(lambda: {
            "partner_id": False,
            "concept_id": False,
            "base_amount": 0.0,
            "tax_amount": 0.0,
            "account_codes": set(),
        })

        for partner_id, concept_id, base_amount, acc_codes in base_rows:
            key = (partner_id, concept_id)
            record = grouped[key]
            record["partner_id"] = partner_id
            record["concept_id"] = concept_id
            record["base_amount"] += base_amount or 0.0
            if acc_codes:
                record["account_codes"].update(
                    [code.strip() for code in acc_codes.split(",")]
                )

        for partner_id, concept_id, tax_amount, acc_codes in tax_rows:
            key = (partner_id, concept_id)
            record = grouped[key]
            record["partner_id"] = partner_id
            record["concept_id"] = concept_id
            record["tax_amount"] += tax_amount or 0.0
            if acc_codes:
                record["account_codes"].update(
                    [code.strip() for code in acc_codes.split(",")]
                )

        if not grouped:
            return []

        # Cargar partners y conceptos para enriquecer info (ORM sobre pocos registros)
        partner_ids = {g["partner_id"] for g in grouped.values() if g["partner_id"]}
        concept_ids = {g["concept_id"] for g in grouped.values() if g["concept_id"]}

        partners = self.env["res.partner"].browse(list(partner_ids))
        concepts = self.env["dian.concepto.mapping"].browse(list(concept_ids))

        partner_map = {p.id: p for p in partners}
        concept_map = {c.id: c for c in concepts}

        lines = []
        for key, rec in grouped.items():
            partner = partner_map.get(rec["partner_id"])
            concept = concept_map.get(rec["concept_id"])
            if not partner or not concept:
                continue

            # NOTA: Ajusta estos campos según tu instalación/l10n_co:
            # - partner.l10n_co_document_type (o similar)
            # - state.dian_code / state.code_dane / state.code, etc.
            # - city.dane_code / city.code_dane / city.code
            # Usa TODO para que lo revises en tu BD.

            doc_type = getattr(partner, "l10n_co_document_type", False) or ""
            # Muchas localizaciones guardan el código en 'code'
            estado = partner.state_id
            municipio = getattr(partner, "city_id", False)  # puede ser res.city
            country = partner.country_id

            line = {
                "concept_code": concept.code or "",
                "concept_name": concept.name or "",
                "account_codes": ", ".join(sorted(rec["account_codes"])) or "",
                "partner_vat": partner.vat or "",
                "partner_name": partner.name or "",
                "partner_street": partner.street or "",
                # Ajustar estos 3 según tu l10n_co:
                "partner_doc_type": doc_type,
                "partner_state_code": getattr(estado, "code_dane", False)
                or getattr(estado, "code", "") or "",
                "partner_city_code": getattr(municipio, "code_dane", False)
                or getattr(municipio, "code", "") or "",
                "partner_country_code": country.code or "",
                # Cálculos
                "base_amount": rec["base_amount"],
                "non_deductible_amount": 0.0,  # TODO: lógica si la tienes
                "tax_amount": rec["tax_amount"],
            }
            lines.append(line)

        # Ordenar por partner y concepto para que se vea bonito como el libro mayor
        lines.sort(key=lambda l: (l["partner_vat"], l["concept_code"]))
        return lines

    # -------------------------------------------------------------------------
    # BOTONES DEL WIZARD
    # -------------------------------------------------------------------------
    def action_view_html(self):
        """Botón: Ver en pantalla (HTML)."""
        self.ensure_one()
        return self.env.ref(
            "l10n_co_dian_1001.action_report_dian_1001"
        ).report_action(self)

    def action_export_xlsx(self):
        """Botón: Descargar Excel (usa controlador HTTP)."""
        self.ensure_one()
        url = "/dian/report/1001/xlsx?wizard_id=%s" % self.id
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }

    # Método usado tanto por QWeb como por el controlador Excel
    def get_report_lines(self):
        self.ensure_one()
        return self._get_grouped_data()
