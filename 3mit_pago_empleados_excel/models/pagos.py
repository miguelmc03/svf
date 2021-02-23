# -*- coding: utf-8 -*-

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
from dateutil.relativedelta import relativedelta

class RegistroDePagosLines(models.Model):
    _name = 'pagos.empleados.lines'

    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Cuenta Contable',
                                 domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]",
                                 help="An expense account is expected", required=True)
    monto_pago = fields.Float(required=True)
    date = fields.Date('Date', default=date.today())
    pagos_id = fields.Many2one('registro.pagos.empleados', 'pagos empleados relacion', ondelete='cascade', index=True)
    tipo_monto = fields.Selection([
        ('D', 'Debe'),
        ('H', 'Haber'),
    ], default='D')
    referencia = fields.Char()
    ctta_analitica_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica')
    partner_id = fields.Many2one('res.partner', string='Empresa')

class RegistroDePagos(models.Model):
    
    _name = 'registro.pagos.empleados'
    
    name = fields.Char()
    state = fields.Selection([
        ('0', 'Borrador'),
        ('1', 'Confirmado'),
        ('2', 'Distribuido al Costo')
    ], default='0')

    @api.model
    def _default_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        return self.env['account.journal'].search(
            [('type', 'in', ['cash', 'bank']), ('company_id', '=', default_company_id)], limit=1)

    date = fields.Date('Date', default=date.today())
    date_from = fields.Date(string='From', required=True,
                            default=lambda self: fields.Date.to_string(date.today().replace(day=1)),)
    date_to = fields.Date(string='To', required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    # account_id_uno = fields.Many2one('account.account', string='Cuenta uno',
    #                              domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]",
    #                              help="An expense account is expected", required=True)
    # account_id_dos = fields.Many2one('account.account', string='Cuenta dos',
    #                                       domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]",
    #                                       help="An expense account is expected" , required=True)
    pagos_ids = fields.One2many('pagos.empleados.lines', 'pagos_id')

    bank_journal_id = fields.Many2one('account.journal', string='Diario del banco',
                                      check_company=True,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_bank_journal_id,
                                      help="Diario de pagos de pagos de empleados.")
    
    movimiento_contable = fields.Many2one('account.move', readonly=True, string="Movimiento contable")
    movimiento_proyectos = fields.Many2one('account.move', readonly=True, string="Movimiento contable Proyectos")
    
    def action_confirm(self):
        if not self.pagos_ids:
            raise UserError('Debe registrar lineas de pagos para poder confirmar')
        monto_total = 0
        for lines in self.pagos_ids:
            monto_total += lines.monto_pago
            if lines.monto_pago == 0:
                raise UserError('Debe registrar todos los montos para procesar el registro de pagos')

        #Se crea el movimiento contable con las cuentas uno y dos
        journal_lines = []
        for lines in self.pagos_ids:

            if lines.tipo_monto == 'H':

                journal_lines.append(
                    (0, 0, {
                        'account_id': lines.account_id.id,
                        'partner_id': '',
                        'name': lines.referencia,
                        'debit': 0.00,
                        'credit': lines.monto_pago,
                        'partner_id': lines.partner_id.id,
                        'analytic_account_id': lines.ctta_analitica_id.id,
                    }),
                )
            if lines.tipo_monto == 'D':
                journal_lines.append(
                    (0, 0, {
                        'account_id': lines.account_id.id,
                        'partner_id': '',
                        'name': lines.referencia,
                        'debit': lines.monto_pago,
                        'credit': 0.00,
                        'partner_id': lines.partner_id.id,
                        'analytic_account_id': lines.ctta_analitica_id.id,
                    }),
                )

        busq_diario = self.bank_journal_id

        journal_item = self.env['account.move'].create({
            'ref': 'Pago de nómina referente a %s' % (self.name),
            'line_ids': journal_lines,
            'type': 'entry',
            'state': 'draft'
        })

        journal_item.action_post()
        self.movimiento_contable = journal_item

        self.state = '1'
        return


    def action_asignar(self):
        # extraigo data de proyectos.
        proyectos = []
        proyectos_ids = self.env['project.project'].search([])
        for pro in proyectos_ids:
            proyectos.append({
                'id_proyecto': pro.id,
                'name_proyecto': pro.name,
                'horas_proyecto': 0,
                'monto_proyecto': 0.00,

            })
        # /////Extraigo por empleado las horas registradas laboradas////////
        for lines in self.pagos_ids:
            coste_hora = lines.empleado_id.timesheet_cost
            if coste_hora == 0 or coste_hora == False:
                raise UserError('El empleado %s, no tiene el coste por hora configurado' % (lines.empleado_id.name))
            registros_trabajado = self.env['account.analytic.line'].search(
                [('employee_id', '=', lines.empleado_id.id), ('company_id', '=', self.company_id.id),
                 ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('task_id', '!=', False)])
            for pro in proyectos:
                for reg in registros_trabajado:
                    if pro.get('id_proyecto') == reg.project_id.id:
                        pro['horas_proyecto'] = pro.get('horas_proyecto') + reg.unit_amount
                        monto = coste_hora * reg.unit_amount
                        pro['monto_proyecto'] = pro.get('monto_proyecto') + monto

        journal_lines = []
        for pro in proyectos:
            if pro.get('monto_proyecto'):
                monto_total = pro.get('monto_proyecto')
                proyectos_id = self.env['project.project'].search([('id', '=', pro.get('id'))])
                if proyectos_id.marca_id:
                    account_first = proyectos_id.marca_id.account_id
                else:
                    account_first = self.env['marcas.model'].search([('name', '=', 'N/A')])

                account_second = self.account_id_dos
                journal_lines.append(
                    (0, 0, {
                        'account_id': account_second.id,
                        'partner_id': '',
                        'name': "Descuento por pagos nomina  %s al proyecto %s" % (self.name, pro.get('name_proyecto')),
                        'debit': 0.00,
                        'credit': monto_total,
                    }),
                )
                journal_lines.append(
                    (0, 0, {
                        'account_id': account_first.id,
                        'partner_id': '',
                        'name': "Gasto por pagos nomina  %s al proyecto %s" % (self.name, pro.get('name_proyecto')),
                        'debit': monto_total,
                        'credit': 0.00,
                    }),
                )

        busq_diario = self.bank_journal_id

        journal_item = self.env['account.move'].create({
            'ref': 'Pago de nómina referente a %s por proyectos' % (self.name),
            'journal_id': busq_diario.id,
            'line_ids': journal_lines,
            'type': 'entry',
            'state': 'draft'
        })

        journal_item.action_post()
        self.movimiento_proyectos = journal_item

        self.state = '2'
        return


    def action_view_movimientos_ids(self):
        self.ensure_one()
        return {
            'name': self.movimiento_contable.name,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': self.movimiento_contable.id,
        }

    def action_view_proyectos_ids(self):
        self.ensure_one()
        return {
            'name': self.movimiento_proyectos.name,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': self.movimiento_proyectos.id,
        }