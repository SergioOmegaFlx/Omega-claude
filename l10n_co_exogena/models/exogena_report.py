# -*- coding: utf-8 -*-
import logging
import base64
from datetime import datetime
from odoo import models, fields, api
from lxml import etree

_logger = logging.getLogger(__name__)

class ExogenaReport(models.Model):
    _name = 'exogena.report' # <-- CAMBIO CLAVE: _name en lugar de _inherit
    _description = 'Lote de Generación de Información Exógena'
    _order = 'create_date desc'

    # --- CAMPOS BASE QUE FALTABAN ---
    name = fields.Char(string="Referencia", readonly=True, required=True, copy=False, default='Nuevo')
    year = fields.Integer(string="Año Fiscal", required=True, readonly=True)
    date_from = fields.Date(string="Desde", required=True, readonly=True)
    date_to = fields.Date(string="Hasta", required=True, readonly=True)
    format_id = fields.Many2one('exogena.format', string="Formato Generado", required=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('processing', 'En Proceso'),
        ('done', 'Hecho'),
        ('error', 'Error'),
    ], string="Estado", default='draft', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string="Compañía", required=True, default=lambda self: self.env.company, readonly=True)
    
    # --- CAMPOS QUE YA TENÍAS (ESTÁN CORRECTOS) ---
    line_f1001_ids = fields.One2many(
        'exogena.report.line.f1001',
        'report_id',
        string="Líneas del Formato 1001"
    )
    xml_file = fields.Binary(string="Archivo XML", readonly=True)
    xml_filename = fields.Char(string="Nombre de Archivo XML", readonly=True)
    send_number = fields.Char(string="Número de Envío", default="1", copy=False)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                format_id = self.env['exogena.format'].browse(vals.get('format_id'))
                vals['name'] = f"{format_id.code} - {vals.get('year')}" or 'Nuevo'
        return super().create(vals_list)

    # --- MÉTODOS QUE YA TENÍAS (ESTÁN PERFECTOS) ---
    # ... (Todos los métodos: _get_dian_document_type, action_export_to_xml,
    #      action_generate_report_data, _get_f1001_query, _generate_f1001_data
    #      permanecen exactamente igual que en tu archivo) ...
    def _get_dian_document_type(self, odoo_code):
        """ Mapea el código de tipo de documento de Odoo al código numérico de la DIAN. """
        mapping = {
            'rut': '31',
            'cedula': '13',
            'tarjeta_identidad': '12',
            'cedula_extranjeria': '22',
            'pasaporte': '41',
            'nit_otro_pais': '42',
            'registro_civil': '11',
            # Añadir más mapeos si son necesarios
        }
        return mapping.get(odoo_code, '43') # 43: Sin identificación o definido por la DIAN

    def action_export_to_xml(self):
        self.ensure_one()
        
        # 1. Crear el elemento raíz del XML
        root_node = etree.Element('mas')
        # Añadir atributos del esquema (opcional pero recomendado)
        root_node.set('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation', 'mas_exogena_v10.xsd')

        # 2. Construir la Cabecera (Cab)
        company = self.company_id
        cab_node = etree.SubElement(root_node, 'Cab')
        etree.SubElement(cab_node, 'Ano').text = str(self.year)
        etree.SubElement(cab_node, 'CodCpt').text = '1001' # Concepto del Formato
        etree.SubElement(cab_node, 'Formato').text = self.format_id.code
        etree.SubElement(cab_node, 'Version').text = self.format_id.version
        etree.SubElement(cab_node, 'NumEnvio').text = self.send_number
        etree.SubElement(cab_node, 'FecEnvio').text = datetime.now().strftime('%Y-%m-%d')
        etree.SubElement(cab_node, 'TipDoc').text = self._get_dian_document_type(company.partner_id.l10n_co_document_type)
        etree.SubElement(cab_node, 'NumDoc').text = company.partner_id.vat
        etree.SubElement(cab_node, 'Dv').text = company.partner_id.l10n_co_verification_digit or ''
        etree.SubElement(cab_node, 'RazonSocial').text = company.partner_id.name
        etree.SubElement(cab_node, 'NumReg').text = str(len(self.line_f1001_ids))

        # 3. Construir los Registros (Reg) para cada línea
        for line in self.line_f1001_ids:
            reg_node = etree.SubElement(root_node, 'Reg')
            partner = line.partner_id
            
            etree.SubElement(reg_node, 'Cpt').text = line.concepto_id.code
            etree.SubElement(reg_node, 'TDoc').text = self._get_dian_document_type(partner.l10n_co_document_type)
            etree.SubElement(reg_node, 'NIdent').text = partner.vat
            
            # Nombres y Apellidos
            if partner.is_company:
                etree.SubElement(reg_node, 'DAp')
                etree.SubElement(reg_node, 'SAp')
                etree.SubElement(reg_node, 'PNom')
                etree.SubElement(reg_node, 'ONom')
                etree.SubElement(reg_node, 'RSoc').text = partner.name
            else:
                etree.SubElement(reg_node, 'DAp').text = partner.l10n_co_name_1 or ''
                etree.SubElement(reg_node, 'SAp').text = partner.l10n_co_name_2 or ''
                etree.SubElement(reg_node, 'PNom').text = partner.l10n_co_firstname or ''
                etree.SubElement(reg_node, 'ONom').text = partner.l10n_co_othername or ''
                etree.SubElement(reg_node, 'RSoc')

            # Dirección y Ubicación
            etree.SubElement(reg_node, 'Dir').text = partner.street or 'NO APLICA'
            etree.SubElement(reg_node, 'CodDpto').text = partner.state_id.l10n_co_dian_code or '00'
            etree.SubElement(reg_node, 'CodMun').text = partner.city_id.l10n_co_dian_code or '000'
            etree.SubElement(reg_node, 'Pais').text = partner.country_id.code or 'CO'

            # Valores Monetarios (redondeados a enteros)
            etree.SubElement(reg_node, 'PagDed').text = str(round(line.pago_deducible))
            etree.SubElement(reg_node, 'PagNoDed').text = str(round(line.pago_no_deducible))
            etree.SubElement(reg_node, 'IvaMayCosDed').text = str(round(line.iva_mayor_valor_costo_deducible))
            etree.SubElement(reg_node, 'IvaMayCosNoDed').text = str(round(line.iva_mayor_valor_costo_no_deducible))
            etree.SubElement(reg_node, 'RetRentaP').text = str(round(line.retencion_renta))
            etree.SubElement(reg_node, 'RetRentaA').text = str(round(line.retencion_renta_asumida))
            etree.SubElement(reg_node, 'RetIvaRC').text = str(round(line.retencion_iva_regimen_comun))
            etree.SubElement(reg_node, 'RetIvaNoDom').text = str(round(line.retencion_iva_practicada_no_domiciliado))

        # 4. Generar el archivo y almacenarlo
        xml_content = etree.tostring(root_node, pretty_print=True, xml_declaration=True, encoding='UTF-8')
        
        filename = f"muisca_{self.format_id.code}v{self.format_id.version}_{self.year}_{self.send_number.zfill(2)}.xml"
        
        self.write({
            'xml_file': base64.b64encode(xml_content),
            'xml_filename': filename,
        })
        
        # 5. Devolver la acción de descarga (opcional, pero mejora la experiencia de usuario)
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{self._name}/{self.id}/xml_file?download=true',
            'target': 'self',
        }



    def action_generate_report_data(self):
        self.ensure_one()
        # Limpiar líneas antiguas si se regenera
        self.line_f1001_ids.unlink()

        # Obtener el valor de la UVT desde el wizard (necesitaremos pasarlo)
        # Por ahora lo buscamos, pero lo ideal es recibirlo como parámetro.
        uvt_record = self.env['exogena.uvt'].search([('year', '=', self.year)], limit=1)
        uvt_value = uvt_record.value if uvt_record else 0

        if self.format_id.code == '1001':
            self._generate_f1001_data(uvt_value)
        
        return True

    def _get_f1001_query(self):
        """ Construye la consulta SQL para agregar los datos base (versión corregida). """
        # Simplificamos la consulta: ya no intentamos obtener tag_ids directamente.
        query = """
            SELECT
                aml.partner_id,
                aml.account_id,
                SUM(aml.debit) as total_debit,
                SUM(aml.credit) as total_credit
            FROM
                account_move_line aml
            WHERE
                aml.parent_state = 'posted'
                AND aml.date BETWEEN %s AND %s
                AND aml.company_id = %s
                AND aml.partner_id IS NOT NULL
            GROUP BY
                aml.partner_id, aml.account_id
        """
        return query

    def _generate_f1001_data(self, uvt_value):
        """ Procesa y crea las líneas para el Formato 1001 (versión corregida). """
        
        # 1. Obtener todos los mapeos de una vez
        mappings = self.env['exogena.concepto.mapping'].search([
            ('concepto_id.format_id', '=', self.format_id.id),
            ('company_id', '=', self.company_id.id)
        ])
        
        # 2. Ejecutar la consulta SQL simplificada
        sql_query = self._get_f1001_query()
        self.env.cr.execute(sql_query, (self.date_from, self.date_to, self.company_id.id))
        results = self.env.cr.dictfetchall()

        # 3. [PASO NUEVO] Obtener las etiquetas de todas las cuentas involucradas de forma eficiente
        account_ids = {res['account_id'] for res in results}
        accounts = self.env['account.account'].browse(list(account_ids))
        account_tags_map = {acc.id: acc.tag_ids.ids for acc in accounts}
        
        # 4. Procesar resultados en un diccionario para agregación
        processed_data = {} # Estructura: {(partner_id, concepto_id): {col_dest: amount}}
        
        for res in results:
            account_id = res['account_id']
            # Obtenemos las etiquetas del mapa que creamos, mucho más rápido
            tag_ids = account_tags_map.get(account_id, [])

            # Buscar el mapeo aplicable para esta línea de la consulta
            for m in mappings:
                is_match = False
                if m.mapping_type == 'account' and account_id in m.account_ids.ids:
                    is_match = True
                # La lógica aquí es más precisa: verificamos si alguna de las etiquetas de la cuenta está en el mapeo
                elif m.mapping_type == 'tag' and m.account_tag_id.id in tag_ids:
                    is_match = True

                if is_match:
                    partner_id = res['partner_id']
                    concepto_id = m.concepto_id.id
                    key = (partner_id, concepto_id)
                    
                    if key not in processed_data:
                        processed_data[key] = {}
                    
                    amount = res['total_debit'] if m.move_type == 'debit' else res['total_credit']
                    
                    col = m.column_dest
                    processed_data[key][col] = processed_data[key].get(col, 0.0) + amount
                    break
        
        # 5. Aplicar topes y crear las líneas del reporte (sin cambios en esta parte)
        lines_to_create = []
        for (partner_id, concepto_id), values in processed_data.items():
            concepto = self.env['exogena.concepto'].browse(concepto_id)
            
            total_pago = values.get('pago_deducible', 0.0) + values.get('pago_no_deducible', 0.0)
            tope_minimo = concepto.threshold_uvt * uvt_value if concepto.threshold_uvt > 0 else 0
            
            if not tope_minimo or total_pago >= tope_minimo:
                line_data = {
                    'report_id': self.id,
                    'partner_id': partner_id,
                    'concepto_id': concepto_id,
                }
                line_data.update(values)
                lines_to_create.append(line_data)
        
        _logger.info(f"Creando {len(lines_to_create)} líneas para el reporte de exógena {self.name}")
        if lines_to_create:
            self.env['exogena.report.line.f1001'].create(lines_to_create)
        
        _logger.info(f"Creando {len(lines_to_create)} líneas para el reporte de exógena {self.name}")
        self.env['exogena.report.line.f1001'].create(lines_to_create)