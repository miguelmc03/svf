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
    _name = "wizard.pagos.excel"

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

        pago_empleado_id = self.env['registro.pagos.empleados'].browse(self._context['active_id'])
        pagos_lines = []
        for lis in list:
            company_id = self._get_company()
            # extraigo la cuenta analitica y cuenta
            if lis[0] and lis[1] and lis[3] and lis[2]:
                account_id = self.env['account.account'].search(
                    [('code_alias', '=', lis[0]), ('company_id', '=', company_id.id)],
                    limit=1)
                if not account_id:
                    raise UserError('No se encuentra la Cuenta con código %s' % (lis[0]))
                monto = float(lis[1])
                if lis[2] != 'D' and lis[2] != 'H':
                    raise UserError('Indique correctamente si es del tipo haber o debit %s' % (lis[2]))
                if lis[4]:
                    ctta_analitica_id = self.env['account.analytic.account'].search(
                    [('id', '=', int(lis[4]))], limit=1)
                    if not ctta_analitica_id:
                        raise UserError('Indique correctamente la cuenta analitica, no se encuentra %s' % (lis[4]))
                    ctta_analitica_id = ctta_analitica_id.id
                else:
                    ctta_analitica_id = False
                if lis[5]:
                    partner_id = self.env['res.partner'].search(
                    [('id', '=', int(lis[5]))], limit=1)
                    if not partner_id:
                        raise UserError('Indique correctamente el campo empresa, no se encuentra %s' % (lis[4]))
                    partner_id = partner_id.id
                else:
                    partner_id = False
                pagos_lines.append(
                    (0, 0, {
                        'account_id': account_id.id,
                        'monto_pago': monto,
                        'date': pago_empleado_id.date,
                        'pagos_id': pago_empleado_id.id,
                        'tipo_monto': lis[2],
                        'referencia': lis[3],
                        'ctta_analitica_id': ctta_analitica_id,
                        'partner_id': partner_id,
                    })
                )
            else:
                raise UserError('Por favor verifique contenga toda la informacion necesaria')

        if pago_empleado_id:
            pago_empleado_id.write({'pagos_ids': pagos_lines})
        return