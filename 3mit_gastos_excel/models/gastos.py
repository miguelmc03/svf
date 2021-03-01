from datetime import datetime, date, timedelta
import locale
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError
from datetime import timedelta, date, datetime
from io import BytesIO
import xlwt, base64
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from operator import itemgetter
import os
from odoo import http
from xlrd import open_workbook
import base64
from odoo.tests import Form, tagged

class GastosCargaExcel(models.TransientModel):
    _name = "wizard.gastos.excel"

    document_origin = fields.Binary()
    name_document = fields.Char()

    @api.model
    def _get_company(self):
        '''Método que busca el id de la compañia'''
        company_id = self.env['res.users'].browse(self.env.uid).company_id
        return company_id

    def carga_data(self):
        datas = open_workbook(file_contents=base64.decodestring(self.document_origin))
        for data in datas.sheets():
            list = []
            for row in range(data.nrows):
                col_value = []
                if row > 0: #ignoro la primera fila
                    for col in range(data.ncols):
                        value = data.cell(row, col).value
                        try:
                            value = str(int(value))
                        except:
                            pass
                        value = value.replace('\n', '')
                        col_value.append(value)
                    list.append(col_value)

        for lis in list:
            company_id = self._get_company()
            # extraigo la cuenta analitica y cuenta
            if lis[1] and lis[2] and lis[4]:
                if lis[0]:
                    proyecto = self.env['project.project'].search([('id', '=', int(lis[0]))])
                    if not proyecto:
                        raise UserError('No se encuentra el proyecto con identificador %s' % (lis[0]))
                    analytic_account_id = proyecto.analytic_account_id
                    if proyecto.marca_id:
                        account_id = proyecto.marca_id.account_id
                    else:
                        if not lis[5]:
                            raise UserError('Por favor indique la cuenta si no tiene un proyecto y marca asociado al proyecto')
                        account_id = self.env['account.account'].search(
                            [('code_alias', '=', lis[5]), ('company_id', '=', company_id.id)],
                            limit=1)
                        if not account_id:
                            raise UserError('No se encuentra la cuenta %s' % (lis[5]))
                else:
                    analytic_account_id = self.env['account.analytic.account'].search(
                        [('id', '=', int(lis[7]))], limit=1)
    
                    if not analytic_account_id:
                        raise UserError('No se encuentra la cuenta analítica %s' % (lis[7]))
                    if not lis[5]:
                        raise UserError('Por favor indique la cuenta si no tiene un proyecto y marca asociado al proyecto')
                    account_id = self.env['account.account'].search(
                        [('code_alias', '=', lis[5]), ('company_id', '=', company_id.id)],
                        limit=1)
                    if not account_id:
                        raise UserError('No se encuentra la cuenta %s' % (lis[5]))
                employee_id = self.env['hr.employee'].search([('identification_id', '=', str(lis[1])), ('company_id', '=', company_id.id)], limit=1)
                if not employee_id:
                    raise UserError('No se encuentra al empleado %s' % (lis[1]))
                if lis[2] == 'L':
                    payment_mode = 'company_account'
                else:
                    payment_mode = 'own_account'
                # analytic_taf_ids = self.env['account.analytic.tag'].search([('name', '=', lis[5])],
                #                                              limit=1)
                product_id = self.env['product.product'].search([('id', '=', int(lis[3]))],
                                                             limit=1)
                if not product_id:
                    raise UserError('No se encuentra el id %s en la lista de productos ' %(lis[3]))
                if not lis[4]:
                    raise UserError('Por favor indique la cantidad')
                quantity = int(lis[4])
                currency_id = self.env['res.currency'].search(
                    [('name', '=', lis[6])],
                    limit=1)
                if not lis[8]:
                    raise UserError('Por favor indique la fecha')
                try:
                    date = datetime.strptime(lis[8], '%d/%m/%Y')
                except:
                    date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(lis[8]) - 2)
                    date = date.date()

                name = str(employee_id.name) + ' ' + product_id.name
                if not lis[9] or not lis[10]:
                    raise UserError('Indique tooso los precios unitarios y totales')
                uuid = lis[11]
                name = lis[12]
                referencia = lis[13]
                if lis[14]:
                    impuesto_id = self.env['account.tax'].search([('amount', '=', float(lis[14])), ('type_tax_use','=','purchase')])
                else:
                    impuesto_id = False
                dic = {
                    'name': name,
                    'employee_id': employee_id.id,
                    'payment_mode': payment_mode,
                    'analytic_account_id': analytic_account_id.id,
                    'company_id': company_id.id,

                    'product_id': product_id.id,
                    'quantity': quantity,
                    'account_id': account_id.id,
                    'currency_id': currency_id.id,
                    'state': 'draft',
                    'date': date,
                    'unit_amount': float(lis[9]),
                    'total_amount': float(lis[10]),
                    'uuid': uuid,
                    'reference': referencia,
                    'tax_ids': impuesto_id
                }
                vb = self.env['hr.expense'].create(dic)
                vb.action_submit_expenses()
                diario_id = self.env['account.journal'].search([('code', '=', 'SIVAL')],
                                                                limit=1)
                if diario_id:
                    vb.sheet_id.bank_journal_id = diario_id
                vb.sheet_id.action_submit_sheet()
                vb.sheet_id.approve_expense_sheets()
                if lis[2] == 'L':
                    vb.sheet_id.action_sheet_move_create()
        return