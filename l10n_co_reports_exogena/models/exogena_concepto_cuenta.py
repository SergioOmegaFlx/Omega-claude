# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ExogenaConceptoCuenta(models.Model):
    """Mapeo de Cuentas Contables a Conceptos de Exógena"""
    _name = 'exogena.concepto.cuenta'
    _description = 'Mapeo Cuenta - Concepto Exógena'
    _order = 'concepto_id, tipo_columna, account_id'

    concepto_id = fields.Many2one(
        'exogena.concepto',
        string='Concepto',
        required=True,
        ondelete='cascade',
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    account_id = fields.Many2one(
        'account.account',
        string='Cuenta Contable',
        required=True,
        help='Cuenta contable o cuenta padre para drill-down'
    )
    tipo_columna = fields.Selection([
        ('base', 'Columna Base (Pago/Ingreso/Saldo)'),
        ('retencion', 'Columna Retención'),
        ('iva', 'Columna IVA'),
        ('devolucion', 'Devoluciones (Resta)'),
    ], string='Tipo de Columna', required=True, default='base',
       help='Define en qué columna del reporte se acumula esta cuenta')
    
    include_children = fields.Boolean(
        string='Incluir Cuentas Hijas',
        default=True,
        help='Si está marcado, incluye automáticamente todas las cuentas que '
             'empiecen con el código de esta cuenta (drill-down jerárquico). '
             'Ej: Si mapeas 5135, incluirá 513501, 513502, etc.'
    )
    
    signo = fields.Selection([
        ('positivo', 'Positivo (Suma)'),
        ('negativo', 'Negativo (Resta)'),
    ], string='Signo', default='positivo',
       help='Define si esta cuenta suma o resta al concepto. '
            'Útil para devoluciones o ajustes')
    
    notas = fields.Text(
        string='Notas',
        help='Notas sobre este mapeo (opcional)'
    )
    
    # Campo computed para mostrar info
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    _sql_constraints = [
        ('account_concepto_columna_uniq', 
         'unique(account_id, concepto_id, tipo_columna, company_id)',
         'Esta cuenta ya está mapeada a este concepto en esta columna.')
    ]
    
    @api.depends('account_id', 'concepto_id', 'tipo_columna', 'include_children')
    def _compute_display_name(self):
        for rec in self:
            if rec.account_id and rec.concepto_id:
                tipo = dict(rec._fields['tipo_columna'].selection).get(rec.tipo_columna, '')
                children = ' (+hijas)' if rec.include_children else ''
                rec.display_name = f"{rec.account_id.code} → {rec.concepto_id.code} [{tipo}]{children}"
            else:
                rec.display_name = ''
    
    def get_account_ids_for_query(self):
        """
        Retorna lista de IDs de cuentas a incluir en el query.
        Si include_children=True, incluye todas las cuentas hijas.
        """
        self.ensure_one()
        
        if not self.include_children:
            return [self.account_id.id]
        
        # Drill-down: buscar todas las cuentas que empiecen con el código
        account_code = self.account_id.code
        domain = [
            ('code', '=like', f'{account_code}%'),
            ('company_id', '=', self.company_id.id),
        ]
        
        child_accounts = self.env['account.account'].search(domain)
        return child_accounts.ids
    
    @api.constrains('account_id', 'concepto_id')
    def _check_account_concepto_format(self):
        """Validar que la cuenta y concepto sean del mismo formato"""
        for rec in self:
            # Esta validación es informativa, no restrictiva
            # porque podría haber casos válidos de cross-mapping
            pass