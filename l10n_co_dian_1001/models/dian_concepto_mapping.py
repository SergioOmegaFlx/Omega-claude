# l10n_co_dian_1001/models/dian_concepto_mapping.py
from odoo import models, fields


class DianConceptoMapping(models.Model):
    _name = "dian.concepto.mapping"
    _description = "DIAN Concept Mapping"

    code = fields.Char(
        string="Código Concepto DIAN",
        required=True,
        help="Ejemplo: 5002",
    )
    name = fields.Char(
        string="Nombre",
        required=True,
        help="Ejemplo: Honorarios",
    )
    format_type = fields.Selection(
        selection=[
            ("1001", "Formato 1001"),
            # Aquí podrías agregar otros formatos DIAN
        ],
        string="Formato DIAN",
        required=True,
        default="1001",
    )
    base_account_ids = fields.Many2many(
        comodel_name="account.account",
        relation="dian_concept_base_account_rel",
        column1="concept_id",
        column2="account_id",
        string="Cuentas Base (Gasto/Costo)",
        help="Cuentas de gasto/costo para calcular pagos o abonos en cuenta.",
    )
    tax_account_ids = fields.Many2many(
        comodel_name="account.account",
        relation="dian_concept_tax_account_rel",
        column1="concept_id",
        column2="account_id",
        string="Cuentas de Retención",
        help="Cuentas de retención en la fuente para este concepto.",
    )

    _sql_constraints = [
        (
            "code_format_unique",
            "unique(code, format_type)",
            "El código del concepto DIAN debe ser único por formato.",
        )
    ]
