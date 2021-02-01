from datetime import datetime, date
from xlrd import open_workbook
import base64
from odoo import models, fields, api
from odoo.exceptions import UserError

class ImportData(models.TransientModel):
    _name = "import.budget.from.excel"

    # Documento de Excel
    excel_document = fields.Binary(string="Documento")
    document_name = fields.Char(string="Nombre del documento")
    crossovered_budget_line = []

    def saveData(self):
        # Importacion data de Excel
        wb = open_workbook(file_contents=base64.decodestring(self.excel_document))
        for s in wb.sheets():
            values = []
            for row in range(s.nrows):
                col_value = []
                for col in range(s.ncols):
                    value = s.cell(row, col).value
                    try:
                        if(col!=0 and col!=1 and col!=5):
                            value = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(value) - 2)
                            hour, minute, second = self.floatHourToTime(value % 1)
                            value = value.replace(hour=hour, minute=minute, second=second)
                            value = value.date()
                    except:
                        pass
                    col_value.append(value)
                values.append(col_value)
        # Compañia del usuario activo
        user_company_id = self._context.get("allowed_company_ids")[0]

        # Datos de todas las posiciones presupuestarias
        account_budget_post_obj = self.env['account.budget.post'].search([('company_id', '=', user_company_id)])
        account_budget_post_ids = [account.id for account in account_budget_post_obj]
        account_budget_post_names = [account.name for account in account_budget_post_obj]

        # Datos de todas las cuentas analiticas
        account_analytic_account_obj = self.env['account.analytic.account'].search([('company_id', '=', user_company_id)])
        account_analytic_account_ids = [account.id for account in account_analytic_account_obj]
        account_analytic_account_names = [account.name for account in account_analytic_account_obj]

        # Presupuesto activo
        crossovered_budget_obj = self.env['crossovered.budget']
        crossovered_budget = crossovered_budget_obj.browse(self._context['active_id'])

        # Registros de lineas añadidas
        records = []
        cont = 0

        for line in values:
            cont += 1
            self.crossovered_budget_line = []

            # Se filtra la primera linea
            if cont!=1:
                # Se evaluan los parametros de la fila
                if(self.filterRow(line[0],line[1],
                                  line[2],
                                  line[3],
                                  line[4],
                                  account_budget_post_names, account_analytic_account_names,
                                  crossovered_budget,cont)):
                    try:
                        amount = float(line[5])
                    except:
                        raise UserError('El monto especificado es erróneo. Revise la celda F%s' % cont)
                    position1 = account_budget_post_names.index(line[0])
                    position2 = account_analytic_account_names.index(line[1])

                    self.createLine(account_budget_post_ids[position1],
                                    account_analytic_account_ids[position2],
                                    line[2].date(),
                                    line[3].date(),
                                    line[4].date(),
                                    amount)

                    crossovered_budget.write({'crossovered_budget_line': self.crossovered_budget_line})



    def filterRow(self,crossoveredBudget,analyticAccount, date_from, date_to, paid_date, budgetNames, accountNames, budget, row):
        print(type(date_from))
        if crossoveredBudget not in budgetNames:
            raise UserError('La posición presupuestaria "%s" no se encuentra registrada' % crossoveredBudget)
        elif analyticAccount not in accountNames:
            raise UserError('La cuenta analítica "%s" no se encuentra registrada' % analyticAccount)
        elif not isinstance(date_from, date):
            raise UserError('El formato de fecha es incorrecto. Revise la celda C%s' % row)
        elif not isinstance(date_to, date):
            raise UserError('El formato de fecha es incorrecto. Revise la celda D%s' % row)
        elif not isinstance(paid_date, date):
            raise UserError('El formato de fecha es incorrecto. Revise la celda E%s' % row)
        elif date_from > date_to:
            raise UserError('La fecha de inicio es mayor a la de cierre. Revise las celdas C%s y D%s' % (row, row))
        elif date_from.date() < budget.date_from or date_from.date() > budget.date_to:
            raise UserError('La fecha especificada está fuera del período del presupuesto. Revise la celda C%s' % row)
        elif date_to.date() < budget.date_from or date_from.date() > budget.date_to:
            raise UserError('La fecha especificada está fuera del período del presupuesto. Revise la celda D%s' % row)
        else:
            return True


    def createLine(self, budgetId, accountId, date_from, date_to, paid_date, amount):
        self.crossovered_budget_line.append(
            (0, 0, {
                'general_budget_id': budgetId,
                'analytic_account_id': accountId,
                'date_from': date_from,
                'date_to': date_to,
                'paid_date': paid_date,
                'planned_amount': amount,
            })
        )

    def floatHourToTime(fh):
        h, r = divmod(fh, 1)
        m, r = divmod(r * 60, 1)
        return (
            int(h),
            int(m),
            int(r * 60),
        )
