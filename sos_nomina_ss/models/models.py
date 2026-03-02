from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    tarifa_riesgos = fields.Selection([
        ('0.522', 'I'),
        ('1.044', 'II'),
        ('2.436', 'III'),
        ('4.35', 'IV'),
        ('6.96', 'V'),
        ('0', 'No Aplica')
    ], string='Tarifa Riesgos', required=True, default='0.522')
    
    arl_id = fields.Many2one('res.partner', string='Administradora de Riesgos Laborales', domain=[('tipo_arl','=',True)])
    afp_id = fields.Many2one('res.partner', string='Administradora de Fondos de Pension', domain=[('tipo_afp','=',True)])
    afc_id = fields.Many2one('res.partner', string='Administradora de Fondos de Cesantias', domain=[('tipo_afc','=',True)])
    eps_id = fields.Many2one('res.partner', string='Entidad Promotora de Salud', domain=[('tipo_eps','=',True)])
    ccf_id = fields.Many2one('res.partner', string='Caja de Compensacion Familiar', domain=[('tipo_ccf','=',True)])
    
class HrSSEntidad(models.Model):
    _inherit = 'res.partner'
    
    tipo_eps = fields.Boolean("Entidad Promotora de Salud")
    tipo_arl = fields.Boolean("Administradora de Riesgos Laborales")
    tipo_afp = fields.Boolean("Administradora de Fondos de Pension")
    tipo_afc = fields.Boolean("Administradora de Fondos de Cesantias")
    tipo_ccf= fields.Boolean("Caja de Compensacion Familiar")

class HrSalaryRuleSS(models.Model):
    _inherit = 'hr.salary.rule'   
    
    tipo_entidad_asociada = fields.Selection([
            ('arl', 'Administradora de Riesgos Laborales'),
            ('afp', 'Administradora de Fondos de Pension'),
            ('afc', 'Administradora de Fondos de Cesantias'),
            ('eps', 'Entidad Promotora de Salud'),
            ('ccf', 'Caja de Compensacion Familiar'),
            ('na', 'No Aplica'),
            ]
            , string='Tipo Entidad Asociada', help="Identifica a que tipo de entidad según el Sistema de Seguridad Social Colombiano está asociada la regla salarial.", 
            required=True, default='na')
    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    def _prepare_line_values(self, line, account_id, date, debit, credit):
        
        register_partner_id = line.partner_id
        partner = register_partner_id.id or self.employee_id.work_contact_id
        
        if line.salary_rule_id.tipo_entidad_asociada:
            if line.salary_rule_id.tipo_entidad_asociada == 'arl':
                partner = self.contract_id.arl_id
            if line.salary_rule_id.tipo_entidad_asociada == 'afp':
                partner = self.contract_id.afp_id
            if line.salary_rule_id.tipo_entidad_asociada == 'afc':
                partner = self.contract_id.afc_id
            if line.salary_rule_id.tipo_entidad_asociada == 'eps':
                partner = self.contract_id.eps_id
            if line.salary_rule_id.tipo_entidad_asociada == 'ccf':
                partner = self.contract_id.ccf_id
        
        return {
            'name': line.name if line.salary_rule_id.split_move_lines else line.salary_rule_id.name,
            'partner_id': partner.id,
            'account_id': account_id,
            'journal_id': line.slip_id.struct_id.journal_id.id,
            'date': date,
            'debit': debit,
            'credit': credit,
            'analytic_distribution': (line.salary_rule_id.analytic_account_id and {line.salary_rule_id.analytic_account_id.id: 100}) or
                                     (line.slip_id.contract_id.analytic_account_id.id and {line.slip_id.contract_id.analytic_account_id.id: 100}),
            'tax_tag_ids': line.debit_tag_ids.ids if account_id == line.salary_rule_id.account_debit.id else line.credit_tag_ids.ids,
        }
