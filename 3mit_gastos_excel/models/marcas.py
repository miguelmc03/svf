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
    account_ingresos_id = fields.Many2one('account.account', string='Cuenta ingresos diferidos',
                                 domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]",
                                 help="An expense account is expected")
class HerenciaProyecto(models.Model):
    _inherit = "project.project"
    
    marca_id = fields.Many2one('marcas.model', required=True)

    @api.model
    def create(self, vals):
        res = super(HerenciaProyecto, self).create(vals)
        if res.sale_order_id and res.sale_order_id.marca_id:
            res.marca_id = res.sale_order_id.marca_id
        if res.sale_order_id and res.sale_order_id.analytic_group_id:
            res.analytic_account_id.group_id = res.sale_order_id.analytic_group_id
        return res

class herenciaventas(models.Model):
    _inherit = "sale.order"

    marca_id = fields.Many2one('marcas.model')
    analytic_group_id = fields.Many2one('account.analytic.group', 'Grupo analítico')

class herenciacompras(models.Model):
    _inherit = "purchase.order"

    @api.model
    def _compute_marca_id(self):
        marca_id = self.env['marcas.model'].search([('name', '=', 'N/A')])
        if not marca_id:
            raise UserError('Por favor configure la marca de nombre "N/A"')
        return marca_id

    marca_id = fields.Many2one('marcas.model', default=_compute_marca_id)

class HerenciaInvoice(models.Model):
    _inherit = "account.move"

    def action_post(self):
        self.check_apunte()
        var = super(HerenciaInvoice, self).action_post()
        return var

    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        res =  super(HerenciaInvoice, self)._onchange_invoice_line_ids()
        self.check_apunte()
        return res

    def check_apunte(self):
        sale_order_id = self.env['purchase.order'].search([('name', '=', self.invoice_origin), ('company_id', '=', self.company_id.id)])
        if sale_order_id and sale_order_id.marca_id.name != 'N/A':
            for lin in self.invoice_line_ids:
                lin.account_id = sale_order_id.marca_id.account_id
        return


