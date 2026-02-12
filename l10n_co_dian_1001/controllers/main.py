# l10n_co_dian_1001/controllers/main.py
import io

from odoo import http
from odoo.http import request


class DianReportController(http.Controller):

    @http.route(
        "/dian/report/1001/xlsx",
        type="http",
        auth="user",
    )
    def get_dian_1001_xlsx(self, wizard_id, **kwargs):
        wizard = request.env["dian.report.wizard"].browse(int(wizard_id))
        if not wizard.exists():
            return request.not_found()

        lines = wizard.get_report_lines()

        # Crear Excel en memoria
        output = io.BytesIO()
        # xlsxwriter viene con Odoo
        import xlsxwriter

        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        worksheet = workbook.add_worksheet("Formato 1001")

        # Estilos básicos
        header_format = workbook.add_format(
            {"bold": True, "text_wrap": True, "border": 1}
        )
        cell_format = workbook.add_format({"border": 1})
        amount_format = workbook.add_format(
            {"border": 1, "num_format": "#,##0.00"}
        )

        # Encabezados DIAN 1001 (tabla plana)
        headers = [
            "CONCEPTO",
            "CUENTA CONTABLE",
            "TIPO DOCUMENTO",
            "IDENTIFICACION",
            "NOMBRE COMPLETO",
            "DIRECCIÓN",
            "CODIGO DPTO",
            "CODIGO MUNICIPIO",
            "PAIS",
            "PAGO O ABONO EN CUENTA DEDUCIBLE",
            "PAGO O ABONO EN CUENTA NO DEDUCIBLE",
            "RETENCION EN LA FUENTE PRACTICADA",
        ]

        row = 0
        col = 0
        for header in headers:
            worksheet.write(row, col, header, header_format)
            col += 1

        # Contenido
        row = 1
        for line in lines:
            worksheet.write(row, 0, line["concept_code"], cell_format)
            worksheet.write(row, 1, line["account_codes"], cell_format)
            worksheet.write(row, 2, line["partner_doc_type"], cell_format)
            worksheet.write(row, 3, line["partner_vat"], cell_format)
            worksheet.write(row, 4, line["partner_name"], cell_format)
            worksheet.write(row, 5, line["partner_street"], cell_format)
            worksheet.write(row, 6, line["partner_state_code"], cell_format)
            worksheet.write(row, 7, line["partner_city_code"], cell_format)
            worksheet.write(row, 8, line["partner_country_code"], cell_format)
            worksheet.write_number(row, 9, line["base_amount"], amount_format)
            worksheet.write_number(
                row, 10, line["non_deductible_amount"], amount_format
            )
            worksheet.write_number(row, 11, line["tax_amount"], amount_format)
            row += 1

        workbook.close()
        output.seek(0)
        filecontent = output.read()

        filename = "DIAN_1001_%s_%s.xlsx" % (wizard.date_from, wizard.date_to)
        headers_http = [
            ("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("Content-Disposition", http.content_disposition(filename)),
        ]
        return request.make_response(filecontent, headers=headers_http)
