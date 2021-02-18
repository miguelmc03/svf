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

class HerenciaFactura(models.Model):
    _inherit = "account.move"


    def action_post(self):
        var = super(HerenciaFactura, self).action_post()
        if self.invoice_origin:
            documento_origen = self.env['sale.order'].search(
                    [('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)])
            if documento_origen:
                for line in documento_origen.order_line:
                    if line.product_template_id.default_code == '12345' and line.product_template_id.income_analytic_account_id and line_bk.product_template_id.expense_analytic_account_id:
                        name = 'Diferencia origen: ' + self.name
                        #PARTE DE INGRESO A APOYO POST VENTA
                        monto = line.price_subtotal
                        cuenta_id = line.product_template_id.income_analytic_account_id.id
                        self.reajuste_apoyo_analytic(name, cuenta_id, monto)
                        #PARTE GASTO A PRODUCTO
                        monto = monto * -1
                        cuenta_id = line_bk.product_template_id.expense_analytic_account_id.id
                        self.reajuste_apoyo_analytic(name, cuenta_id, monto)
                    else:
                        line_bk = line

        return var


    def reajuste_apoyo_analytic(self, name, cuenta_id, monto):

        data = {
            'name': name,
            'account_id': cuenta_id,
            'date': self.create_date,
            'amount': monto,
        }

        self.env['account.analytic.line'].create(data)

        return