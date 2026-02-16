# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ExogenaConcepto(models.Model):
    """Conceptos DIAN por formato de Información Exógena"""
    _name = 'exogena.concepto'
    _description = 'Concepto de Información Exógena'
    _order = 'formato_id, code'

    code = fields.Char(
        string='Código',
        required=True,
        index=True,
        help='Código del concepto según DIAN (ej: 5002 para Honorarios en F1001)'
    )
    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del concepto (ej: Honorarios, Servicios, etc.)'
    )
    formato_id = fields.Many2one(
        'exogena.formato',
        string='Formato',
        required=True,
        ondelete='cascade',
        help='Formato al que pertenece este concepto'
    )
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    # Configuración de columnas según formato
    # Estas columnas se usan para la lógica de cálculo en el reporte
    columna_base = fields.Selection([
        ('debit_credit', 'Débito - Crédito'),
        ('credit_debit', 'Crédito - Débito'),
        ('balance', 'Saldo (Balance)'),
        ('debit', 'Solo Débitos'),
        ('credit', 'Solo Créditos'),
    ], string='Cálculo Columna Base', 
       help='Fórmula para calcular el monto principal del concepto')
    
    columna_retencion = fields.Selection([
        ('debit_credit', 'Débito - Crédito'),
        ('credit_debit', 'Crédito - Débito'),
        ('balance', 'Saldo (Balance)'),
        ('debit', 'Solo Débitos'),
        ('credit', 'Solo Créditos'),
    ], string='Cálculo Columna Retención',
       help='Fórmula para calcular la retención (si aplica)')
    
    # Mapeo de cuentas
    cuenta_ids = fields.One2many(
        'exogena.concepto.cuenta',
        'concepto_id',
        string='Mapeo de Cuentas'
    )
    
    # Threshold de reporte (cuantías menores)
    threshold_amount = fields.Float(
        string='Tope Mínimo (COP)',
        default=0.0,
        help='Monto mínimo para reportar individualmente. '
             'Valores menores se agrupan en NIT 222222222'
    )
    
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción del concepto y su uso'
    )
    
    _sql_constraints = [
        ('code_formato_uniq', 'unique(code, formato_id)', 
         'El código debe ser único por formato.')
    ]
    
    def name_get(self):
        result = []
        for rec in self:
            name = f"[{rec.code}] {rec.name}"
            result.append((rec.id, name))
        return result
    
    @api.onchange('formato_id')
    def _onchange_formato_id(self):
        """Sugerir configuración predeterminada según formato"""
        if not self.formato_id:
            return
        
        # Configuraciones predeterminadas por formato
        defaults = {
            '1001': {  # Costos y Gastos
                'columna_base': 'debit_credit',
                'columna_retencion': 'credit_debit',
            },
            '1003': {  # Retenciones que practicaron
                'columna_base': 'debit_credit',
                'columna_retencion': False,
            },
            '1005': {  # IVA Descontable
                'columna_base': 'debit_credit',
                'columna_retencion': False,
            },
            '1006': {  # IVA Generado
                'columna_base': 'credit_debit',
                'columna_retencion': False,
            },
            '1007': {  # Ingresos
                'columna_base': 'credit_debit',
                'columna_retencion': False,
            },
            '1008': {  # CxC
                'columna_base': 'balance',
                'columna_retencion': False,
            },
            '1009': {  # CxP
                'columna_base': 'balance',
                'columna_retencion': False,
            },
        }
        
        formato_code = self.formato_id.code
        if formato_code in defaults:
            self.columna_base = defaults[formato_code]['columna_base']
            self.columna_retencion = defaults[formato_code]['columna_retencion']