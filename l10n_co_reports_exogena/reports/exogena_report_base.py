# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import SQL
from collections import defaultdict
import logging

_logger = logging.getLogger(__name__)

class ExogenaReportBase(models.AbstractModel):
    """
    Clase base para todos los reportes de Información Exógena.
    Hereda de account.report para aprovechar el motor dinámico de Odoo 18.
    """
    _name = 'exogena.report.base'
    _description = 'Reporte Base de Información Exógena'
    #_inherit = 'account.report'
    
    # Configuración del reporte
    # filter_date = {'mode': 'range', 'filter': 'this_year'}
    # filter_all_entries = False  # Solo asientos contabilizados
    # filter_unfold_all = False
    #filter_multi_company = None   Una compañía a la vez
    
    # Configuración de cuantías menores
    CUANTIAS_MENORES_NIT = '222222222'
    CUANTIAS_MENORES_NAME = 'CUANTIAS MENORES'
    
    # =========================================================================
    # MÉTODOS ABSTRACTOS - Deben ser implementados por cada formato
    # =========================================================================
    
    def _get_formato_code(self):
        """Retorna el código del formato (ej: '1001', '1003')"""
        raise NotImplementedError("Debe implementar _get_formato_code()")
    
    def _get_columns_name(self, options):
        """Define las columnas del reporte"""
        raise NotImplementedError("Debe implementar _get_columns_name()")
    
    def _get_column_keys(self):
        """
        Retorna lista de keys de columnas monetarias del reporte.
        Ej: ['base', 'retencion'] para F1001
        """
        raise NotImplementedError("Debe implementar _get_column_keys()")
    
    # =========================================================================
    # MÉTODO PRINCIPAL - Generación de Líneas del Reporte
    # =========================================================================
    
    @api.model
    def _get_lines(self, options, line_id=None):
        """
        Método principal que genera las líneas del reporte.
        Este método es llamado por el framework de account.report.
        
        Estructura jerárquica:
        CONCEPTO 5002 - Honorarios
        ├─ Partner 1 (Juan Pérez)
        │  ├─ Base: 10,000,000
        │  └─ Retención: 1,000,000
        └─ Partner 2 (María Gómez)
           ├─ Base: 5,000,000
           └─ Retención: 500,000
        """
        lines = []
        
        # Si se está expandiendo un concepto específico, mostrar sus partners
        if line_id:
            return self._get_partner_lines(options, line_id)
        
        # Obtener datos agrupados por concepto y partner
        data = self._get_report_data(options)
        
        # Generar líneas por concepto
        for concepto_id, concepto_data in data.items():
            concepto = self.env['exogena.concepto'].browse(concepto_id)
            
            # Calcular totales del concepto
            totales = self._calculate_concepto_totals(concepto_data)
            
            # Línea del concepto (expandible)
            concepto_line = self._get_concepto_line(concepto, totales, options)
            lines.append(concepto_line)
        
        return lines
    
    # =========================================================================
    # EXTRACCIÓN DE DATOS - SQL OPTIMIZADO
    # =========================================================================
    
    def _get_report_data(self, options):
        """
        Extrae y procesa datos de account.move.line usando SQL optimizado.
        
        Retorna estructura:
        {
            concepto_id: {
                partner_id: {
                    'base': amount,
                    'retencion': amount,
                    'iva': amount,
                    ...
                }
            }
        }
        """
        date_from = options['date']['date_from']
        date_to = options['date']['date_to']
        company_id = self.env.company.id
        formato_code = self._get_formato_code()
        
        # Obtener formato y conceptos
        formato = self.env['exogena.formato'].search([
            ('code', '=', formato_code)
        ], limit=1)
        
        if not formato:
            _logger.warning(f"Formato {formato_code} no encontrado")
            return {}
        
        conceptos = self.env['exogena.concepto'].search([
            ('formato_id', '=', formato.id),
            ('active', '=', True)
        ])
        
        if not conceptos:
            _logger.warning(f"No hay conceptos configurados para formato {formato_code}")
            return {}
        
        # Estructura de datos
        data = defaultdict(lambda: defaultdict(lambda: {key: 0.0 for key in self._get_column_keys()}))
        
        # Procesar cada concepto
        for concepto in conceptos:
            self._process_concepto_data(concepto, date_from, date_to, company_id, formato, data)
        
        # Aplicar threshold de cuantías menores
        data = self._apply_cuantias_menores(data, conceptos)
        
        return data
    
    def _process_concepto_data(self, concepto, date_from, date_to, company_id, formato, data):
        """Procesa datos de un concepto específico"""
        
        # Obtener mapeos de cuentas
        mapeos = self.env['exogena.concepto.cuenta'].search([
            ('concepto_id', '=', concepto.id),
            ('company_id', '=', company_id)
        ])
        
        if not mapeos:
            return
        
        # Procesar cada mapeo (base, retención, etc.)
        for mapeo in mapeos:
            account_ids = mapeo.get_account_ids_for_query()
            
            if not account_ids:
                continue
            
            # Query SQL optimizado
            query_result = self._execute_account_query(
                account_ids, date_from, date_to, company_id, 
                concepto, mapeo, formato
            )
            
            # Acumular resultados en la estructura de datos
            self._accumulate_query_results(
                query_result, concepto.id, mapeo, data
            )
    
    def _execute_account_query(self, account_ids, date_from, date_to, company_id, concepto, mapeo, formato):
        """
        Ejecuta query SQL optimizado para extraer saldos.
        Maneja tanto reportes de flujo como de saldo.
        """
        # Determinar si es reporte de flujo o saldo
        is_saldo_report = formato.tipo_dato == 'saldo'
        
        if is_saldo_report:
            # Para reportes de saldo (CxC, CxP): calcular saldo acumulado
            query = """
                SELECT 
                    aml.partner_id,
                    SUM(aml.debit) as total_debit,
                    SUM(aml.credit) as total_credit,
                    SUM(aml.balance) as total_balance
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE 
                    aml.account_id IN %s
                    AND am.state = 'posted'
                    AND aml.date <= %s
                    AND am.company_id = %s
                    AND aml.partner_id IS NOT NULL
                GROUP BY aml.partner_id
                HAVING ABS(SUM(aml.balance)) > 0.01
            """
            params = (tuple(account_ids), date_to, company_id)
        else:
            # Para reportes de flujo: solo movimientos del período
            query = """
                SELECT 
                    aml.partner_id,
                    SUM(aml.debit) as total_debit,
                    SUM(aml.credit) as total_credit,
                    SUM(aml.balance) as total_balance
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE 
                    aml.account_id IN %s
                    AND am.state = 'posted'
                    AND aml.date >= %s
                    AND aml.date <= %s
                    AND am.company_id = %s
                    AND aml.partner_id IS NOT NULL
                GROUP BY aml.partner_id
            """
            params = (tuple(account_ids), date_from, date_to, company_id)
        
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()
    
    def _accumulate_query_results(self, query_result, concepto_id, mapeo, data):
        """Acumula resultados del query en la estructura de datos"""
        
        # Determinar cálculo según configuración del concepto
        concepto = self.env['exogena.concepto'].browse(concepto_id)
        tipo_columna = mapeo.tipo_columna
        
        # Mapear tipo_columna a key de columna
        column_key = self._map_tipo_columna_to_key(tipo_columna)
        
        # Determinar fórmula de cálculo
        if tipo_columna == 'base':
            calculo = concepto.columna_base
        elif tipo_columna == 'retencion':
            calculo = concepto.columna_retencion
        else:
            calculo = 'balance'  # Default
        
        signo = 1 if mapeo.signo == 'positivo' else -1
        
        # Acumular por partner
        for row in query_result:
            partner_id = row['partner_id']
            
            # Calcular monto según fórmula
            if calculo == 'debit_credit':
                amount = row['total_debit'] - row['total_credit']
            elif calculo == 'credit_debit':
                amount = row['total_credit'] - row['total_debit']
            elif calculo == 'balance':
                amount = row['total_balance']
            elif calculo == 'debit':
                amount = row['total_debit']
            elif calculo == 'credit':
                amount = row['total_credit']
            else:
                amount = 0.0
            
            # Aplicar signo
            amount *= signo
            
            # Acumular en estructura
            data[concepto_id][partner_id][column_key] += amount
    
    def _map_tipo_columna_to_key(self, tipo_columna):
        """Mapea tipo_columna del mapeo a key de columna del reporte"""
        mapping = {
            'base': 'base',
            'retencion': 'retencion',
            'iva': 'iva',
            'devolucion': 'devolucion',
        }
        return mapping.get(tipo_columna, 'base')
    
    # =========================================================================
    # CUANTÍAS MENORES
    # =========================================================================
    
    def _apply_cuantias_menores(self, data, conceptos):
        """
        Agrupa partners que no superen el threshold bajo NIT 222222222
        """
        new_data = defaultdict(lambda: defaultdict(lambda: {key: 0.0 for key in self._get_column_keys()}))
        
        for concepto in conceptos:
            concepto_id = concepto.id
            threshold = concepto.threshold_amount
            
            if concepto_id not in data:
                continue
            
            # Partner especial para cuantías menores
            cuantias_menores_id = self._get_or_create_cuantias_menores_partner()
            
            for partner_id, amounts in data[concepto_id].items():
                # Calcular total para decisión de threshold
                total = sum(abs(v) for v in amounts.values())
                
                if threshold > 0 and total < threshold:
                    # Acumular en cuantías menores
                    for key, value in amounts.items():
                        new_data[concepto_id][cuantias_menores_id][key] += value
                else:
                    # Mantener partner individual
                    new_data[concepto_id][partner_id] = amounts.copy()
        
        return new_data
    
    def _get_or_create_cuantias_menores_partner(self):
        """Obtiene o crea el partner de cuantías menores"""
        partner = self.env['res.partner'].search([
            ('vat', '=', self.CUANTIAS_MENORES_NIT)
        ], limit=1)
        
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.CUANTIAS_MENORES_NAME,
                'vat': self.CUANTIAS_MENORES_NIT,
                'is_company': True,
                'l10n_co_document_type': 'rut',
                'active': True,
            })
        
        return partner.id
    
    # =========================================================================
    # GENERACIÓN DE LÍNEAS VISUALES
    # =========================================================================
    
    def _get_concepto_line(self, concepto, totales, options):
        """Genera línea visual del concepto (expandible)"""
        columns = []
        
        # Crear columnas según keys definidas
        for key in self._get_column_keys():
            amount = totales.get(key, 0.0)
            columns.append(self._build_column_dict(amount, options))
        
        return {
            'id': f'concepto_{concepto.id}',
            'name': f'[{concepto.code}] {concepto.name}',
            'level': 0,
            'unfoldable': True,
            'unfolded': False,
            'columns': columns,
            'class': 'total',
        }
    
    def _calculate_concepto_totals(self, concepto_data):
        """Calcula totales de un concepto sumando todos sus partners"""
        totales = {key: 0.0 for key in self._get_column_keys()}
        
        for partner_id, amounts in concepto_data.items():
            for key, value in amounts.items():
                totales[key] += value
        
        return totales
    
    def _get_partner_lines(self, options, line_id):
        """Genera líneas de partners cuando se expande un concepto"""
        lines = []
        
        # Extraer concepto_id del line_id
        concepto_id = int(line_id.split('_')[1])
        
        # Obtener datos del reporte
        data = self._get_report_data(options)
        
        if concepto_id not in data:
            return lines
        
        # Ordenar partners por monto total (descendente)
        partners_data = data[concepto_id]
        sorted_partners = sorted(
            partners_data.items(),
            key=lambda x: sum(abs(v) for v in x[1].values()),
            reverse=True
        )
        
        # Generar línea por cada partner
        for partner_id, amounts in sorted_partners:
            partner = self.env['res.partner'].browse(partner_id)
            
            columns = []
            for key in self._get_column_keys():
                amount = amounts.get(key, 0.0)
                columns.append(self._build_column_dict(amount, options))
            
            # Formatear identificación del partner
            partner_info = self._format_partner_info(partner)
            
            lines.append({
                'id': f'partner_{concepto_id}_{partner_id}',
                'name': partner_info,
                'level': 1,
                'parent_id': line_id,
                'columns': columns,
                'caret_options': 'partner',  # Permite drill-down a movimientos
            })
        
        return lines
    
    def _format_partner_info(self, partner):
        """Formatea información del partner para display"""
        vat = partner.vat or 'Sin NIT'
        doc_type = dict(partner._fields['l10n_co_document_type'].selection).get(
            partner.l10n_co_document_type, ''
        ) if hasattr(partner, 'l10n_co_document_type') else ''
        
        return f"{partner.name} | {doc_type} {vat}"
    
    def _build_column_dict(self, amount, options):
        """Construye diccionario de columna con formato"""
        return {
            'name': self.format_value(amount, blank_if_zero=True),
            'no_format': amount,
            'class': 'number',
        }
    
    # =========================================================================
    # EXPORTACIÓN
    # =========================================================================
    
    def _get_report_name(self):
        """Nombre del reporte para exportación"""
        formato_code = self._get_formato_code()
        return f"Formato_{formato_code}_Exogena"
