# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountAccount(models.Model):
    """Extensión de account.account para mostrar mapeos de exógena"""
    _inherit = 'account.account'
    
    exogena_mapeo_ids = fields.One2many(
        'exogena.concepto.cuenta',
        'account_id',
        string='Mapeos Exógena',
        help='Conceptos de exógena a los que está mapeada esta cuenta'
    )
    
    exogena_mapeo_count = fields.Integer(
        string='# Mapeos Exógena',
        compute='_compute_exogena_mapeo_count'
    )
    
    def _compute_exogena_mapeo_count(self):
        for account in self:
            account.exogena_mapeo_count = len(account.exogena_mapeo_ids)