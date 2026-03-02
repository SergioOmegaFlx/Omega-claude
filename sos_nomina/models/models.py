from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class HrContract(models.Model):
    _inherit = 'hr.contract'

    auxilio_transporte = fields.Selection([
        ('no_tte','No Aplica'),
        ('en_dinero', 'En Dinero'),
        ('especie', 'En Especie'),
        ('menor_2', 'Menor a 2 SMLMV')
    ], string='Auxilio de Transporte', required=True, default='menor_2')
    
    schedule_pay = fields.Selection(selection_add=[('quincenal', 'Quincenal')])

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'    

    def compute_rule(self, localdict):
        contract_obj = self.env['hr.contract']
        payslip_obj = self.env['hr.payslip']
        return super(HrSalaryRule, self).compute_rule(localdict)

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    payslip_run_id = fields.Many2one('hr.payslip.run', string="Lote", related='payslip_id.payslip_run_id', readonly=True)

    @api.depends('work_entry_type_id', 'number_of_days', 'number_of_hours', 'payslip_id')
    def _compute_name(self):
        for worked_days in self:
            if worked_days.payslip_id:
                to_check_public_holiday = {
                res[0]: res[1]
                for res in self.env['resource.calendar.leaves']._read_group(
                    [
                        ('resource_id', '=', False),
                        ('work_entry_type_id', 'in', self.mapped('work_entry_type_id').ids),
                        ('date_from', '<=', max(self.payslip_id.mapped('date_to'))),
                        ('date_to', '>=', min(self.payslip_id.mapped('date_from'))),
                    ],
                    ['work_entry_type_id'],
                    ['id:recordset']
                    )
                }
                for worked_days in self:
                    public_holidays = to_check_public_holiday.get(worked_days.work_entry_type_id, '')
                    holidays = public_holidays and public_holidays.filtered(lambda p:
                    (p.calendar_id.id == worked_days.payslip_id.contract_id.resource_calendar_id.id or not p.calendar_id.id)
                        and p.date_from.date() <= worked_days.payslip_id.date_to
                        and p.date_to.date() >= worked_days.payslip_id.date_from
                        and p.company_id == worked_days.payslip_id.company_id)
                    if holidays:
                        name = (', '.join(holidays.mapped('name')))
                    else:
                        name = worked_days.work_entry_type_id.name

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    payslip_run_id = fields.Many2one('hr.payslip.run', string="Lote", related='payslip_id.payslip_run_id', readonly=True)