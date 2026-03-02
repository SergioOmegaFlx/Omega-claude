from odoo import models, fields, api
from odoo.exceptions import UserError

class PilaAsientoWizard(models.TransientModel):
    _name = 'pila.asiento.wizard'
    _description = 'Generador de Asiento Contable PILA'

    month = fields.Selection([
        ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'),
        ('5', 'Mayo'), ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'),
        ('9', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ], string='Mes a Liquidar', required=True, default=str(fields.Date.today().month))
    
    year = fields.Integer(string='Año', required=True, default=fields.Date.today().year)
    date_move = fields.Date(string='Fecha del Asiento', required=True, default=fields.Date.today())
    journal_id = fields.Many2one('account.journal', string='Diario Contable', required=True)

    def generar_asiento_pila(self):
        # 1. Buscar nóminas confirmadas del mes seleccionado
        import calendar
        last_day = calendar.monthrange(self.year, int(self.month))[1]
        date_start = fields.Date.to_date(f'{self.year}-{self.month}-01')
        date_end = fields.Date.to_date(f'{self.year}-{self.month}-{last_day}')

        payslips = self.env['hr.payslip'].search([
            ('date_from', '>=', date_start),
            ('date_to', '<=', date_end),
            ('state', '=', 'done')
        ])

        if not payslips:
            raise UserError('No se encontraron nóminas confirmadas para este periodo.')

        # 2. Validación de Cuentas Contables y Agrupación
        movimientos = {} # {(account_id, partner_id): total}
        total_pago = 0
        reglas_sin_cuenta = set() # Usamos set para no repetir nombres de reglas
        codigos_pila = [
            'AS', 'AS_PAT', 'AP', 'PEN_PAT', 'ARL', 'CCF', 'SENA', 'ICBF',
            'PROV_PRIMA', 'PROV_CESANTIAS', 'PROV_INT_CESANTIAS', 'PROV_VACACIONES',
            'PRI', 'CES', 'ICES'
        ]

        for slip in payslips:
            for line in slip.line_ids.filtered(lambda l: l.code in codigos_pila):
                # Verificamos primero si la regla tiene cuenta de crédito
                if not line.salary_rule_id.account_credit:
                    reglas_sin_cuenta.add(f"[{line.code}] {line.name}")
                    continue

                # Determinar el tercero (Partner)
                partner = False
                if line.code in ['AS', 'AS_PAT']: 
                    partner = slip.contract_id.eps_id
                elif line.code in ['AP', 'PEN_PAT']: 
                    partner = slip.contract_id.afp_id
                elif line.code == 'ARL': 
                    partner = slip.contract_id.arl_id
                elif line.code in ['CCF', 'SENA', 'ICBF']: 
                    partner = slip.contract_id.ccf_id
                
                # Para provisiones o liquidaciones usamos la AFP como tercero por defecto si aplica
                elif line.code in ['PROV_PRIMA', 'PROV_CESANTIAS', 'PROV_INT_CESANTIAS', 'PROV_VACACIONES', 'PRI', 'CES', 'ICES']:
                    partner = slip.contract_id.afp_id

                if not partner:
                    continue

                account_id = line.salary_rule_id.account_credit.id
                key = (account_id, partner.id)
                
                valor = abs(line.total)
                movimientos[key] = movimientos.get(key, 0) + valor
                total_pago += valor

        # Si se detectaron reglas sin cuenta, lanzamos el error antes de crear el asiento
        if reglas_sin_cuenta:
            msj = "Las siguientes reglas salariales están presentes en las nóminas pero NO tienen configurada una 'Cuenta de Crédito':\n\n"
            for regla in reglas_sin_cuenta:
                msj += f"• {regla}\n"
            msj += "\nPor favor, asigne las cuentas contables en Configuración > Reglas Salariales y vuelva a intentar."
            raise UserError(msj)

        # 3. Crear las líneas del asiento (Credits - Detalle Entidades)
        line_ids = []
        for (acc_id, part_id), total in movimientos.items():
            line_ids.append((0, 0, {
                'name': f'Aportes PILA {self.month}/{self.year}',
                'partner_id': part_id,
                'account_id': acc_id,
                'debit': 0.0,
                'credit': total,
            }))

        # 4. Línea de Contrapartida (Debito - SOI Enlace Operativo)
        partner_soi = self.env['res.partner'].search([('vat', '=', '900089104')], limit=1)
        account_soi = self.env['account.account'].search([('code', '=', '23359502')], limit=1)

        if not partner_soi or not account_soi:
            raise UserError('Configure el contacto SOI (NIT 900089104) y la cuenta 23359502 antes de continuar.')

        line_ids.append((0, 0, {
            'name': f'PAGO TOTAL PILA MES {self.month} - SOI',
            'partner_id': partner_soi.id,
            'account_id': account_soi.id,
            'debit': total_pago,
            'credit': 0.0,
        }))

        # 5. Crear el asiento contable (Account Move)
        move = self.env['account.move'].create({
            'journal_id': self.journal_id.id,
            'date': self.date_move,
            'ref': f'PILA_{self.month}_{self.year}',
            'move_type': 'entry',
            'line_ids': line_ids,
        })

        return {
            'name': 'Asiento PILA Generado',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': move.id,
            'type': 'ir.actions.act_window',
        }