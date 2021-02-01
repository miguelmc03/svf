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

class herenciagastos(models.Model):
    _inherit = "hr.expense"  
    uuid = fields.Char()

class Marcas(models.Model):
    _name = "marcas.model"


    name = fields.Char(String="Nombre")
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Cuenta Gasto', domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]", help="An expense account is expected", required=True)
    account_ingresos_id = fields.Many2one('account.account', string='Cuenta Ingresos',
                                 domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]",
                                 help="An expense account is expected")
class HerenciaProyecto(models.Model):
    _inherit = "project.project"
    
    marca_id = fields.Many2one('marcas.model')

    @api.model
    def create(self, vals):
        res = super(HerenciaProyecto, self).create(vals)
        if res.sale_order_id and res.sale_order_id.marca_id:
            res.marca_id = res.sale_order_id.marca_id
        return res

class herenciaventas(models.Model):
    _inherit = "sale.order"

    marca_id = fields.Many2one('marcas.model')