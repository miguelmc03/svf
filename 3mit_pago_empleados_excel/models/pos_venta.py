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

class RegistroDePosVentaLines(models.Model):
    _name = 'pagos.posventa.lines'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    pagos_id = fields.Many2one('registro.pagos.posventa', 'pagos posventa relacion', ondelete='cascade', index=True)
    proyecto_id = fields.Many2one('project.project', string='Proyecto', required=True, readonly=True)
    marca_id = fields.Many2one('marcas.model', string='Marca', required=True, readonly=True)
    horas = fields.Float(string="Horas")
    monto = fields.Float(string="Monto")
    total_gastos = fields.Float(string="Monto gastos")
    date = fields.Date('Date', default=date.today())

class RegistroDePagosPosVenta(models.Model):
    
    _name = 'registro.pagos.posventa'
    
    name = fields.Char()
    state = fields.Selection([
        ('0', 'Borrador'),
        ('1', 'Calculado'),
        ('2', 'Distribuido al Costo')
    ], default='0')

    @api.model
    def _default_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        return self.env['account.journal'].search(
            [('type', 'in', ['cash', 'bank']), ('company_id', '=', default_company_id)], limit=1)

    date = fields.Date('Date', default=date.today())

    date_from = fields.Date(string='From', required=True,
                            default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(months=-1, day=1)).date()))
    date_to = fields.Date(string='To', required=True,
                          default=lambda self: fields.Date.to_string(
                              (datetime.now() + relativedelta(day=1, days=-1)).date()))
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True,
                                 default=lambda self: self.env.company)
   
    pagos_ids = fields.One2many('pagos.posventa.lines', 'pagos_id')

    bank_journal_id = fields.Many2one('account.journal', string='Diario del banco',
                                      check_company=True,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_bank_journal_id,
                                      help="Diario de pagos de pagos de empleados.")
    account_id = fields.Many2one('account.account', string='Cuenta Contable',
                                 domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]",
                                 help="An expense account is expected", required=True)
    movimiento_proyectos = fields.Many2one('account.move', readonly=True, string="Movimiento contable Proyectos")
    
    def action_confirm(self):
        #Valido que existan nominas en ese período de tiempo
        #descomentar esto
        # registros_nominas = self.env['registro.pagos.empleados'].search(
        #     [('company_id', '=', self.company_id.id),
        #      ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', '1')])
        # if not registros_nominas:
        #     raise UserError(
        #         'Debe existir registros de carga de pagos por nómina confirmados en el lapso de tiempo señalado para continuar')
        # extraigo data de proyectos.
        proyectos = []
        pagos_lines = []
        proyectos_ids = self.env['project.project'].search([])

        marca_default_id = self.env['marcas.model'].search([('name', '=', 'N/A')])
        for pro in proyectos_ids:
            if pro.marca_id:
                marca = pro.marca_id.id
            else:
                if not marca_default_id:
                    raise UserError('Por favor registre un marca con nombre "N/A" para los proyectos que no tengan marca asociada.')
                marca = marca_default_id.id
            proyectos.append({
                'id_proyecto': pro.id,
                'name_proyecto': pro.name,
                'horas_proyecto': 0,
                'monto_proyecto': 0.00,
                'marca_id': marca,
                'analytic_account_id': pro.analytic_account_id.id,
                'total_gastos': 0.00,

            })
        # /////Extraigo por empleado las horas registradas laboradas////////
        #coste_hora = 25  # prueba manual

        # if coste_hora == 0 or coste_hora == False:
        #     raise UserError('Por favor registre un coste de hora.')
        for pro in proyectos:
            #Tambien se puede filtrar por el cambo "is_timesheet" que es un booleano
            registros_trabajado = self.env['account.analytic.line'].search(
                [('project_id', '=', pro.get('id_proyecto')), ('company_id', '=', self.company_id.id),
                 ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('task_id', '!=', False), ('employee_id', '!=', False)])
            for reg in registros_trabajado:
                pro['horas_proyecto'] = pro.get('horas_proyecto') + reg.unit_amount
                #monto = reg.employee_id.coste_hora * reg.unit_amount
                if reg.amount < 0:
                    monto = reg.amount * -1
                else:
                    monto = reg.amount
                pro['monto_proyecto'] = pro.get('monto_proyecto') + monto
            gastos_registros = self.env['account.analytic.line'].search(
                [('id', '=', pro.get('id_proyecto')), ('company_id', '=', self.company_id.id),
                 ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('task_id', '!=', False),
                 ('employee_id', '!=', False)])
            registros_trabajados = self.env['account.analytic.line'].search(
                [('account_id', '=', pro.get('analytic_account_id')), ('company_id', '=', self.company_id.id),
                 ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('is_timesheet', '=', False), ('ref', '!=', False)])
            for reg in registros_trabajados:
                gasto_id = self.env['hr.expense'].search([('name', '=', reg.ref)])
                if gasto_id and reg.amount < 0:
                    monto_gastos = reg.amount * -1
                    pro['total_gastos'] = pro.get('total_gastos') + monto_gastos


        for pro in proyectos:
            if pro.get('monto_proyecto'):
                pagos_lines.append(
                    (0, 0, {
                        'name': 'registros referente: ' + self.name,
                        'proyecto_id': pro.get('id_proyecto'),
                        'marca_id': pro.get('marca_id'),
                        'date': self.date,
                        'monto': pro.get('monto_proyecto'),
                        'horas': pro.get('horas_proyecto'),
                        'pagos_id': self.id,
                        'total_gastos': pro.get('total_gastos'),
                    })
                )
        self.write({'pagos_ids': pagos_lines})
        if not pagos_lines:
            raise UserError('No existen registros de horas por proyectos en este lapso de tiempo')
        self.state = '1'
        return



    def action_asignar(self):
        journal_lines = []
        credit = debit = 0
        for pro in self.pagos_ids:
            monto_total = pro.monto
            account_first = pro.marca_id.account_id
            credit += monto_total
            journal_lines.append(
                (0, 0, {
                    'account_id': account_first.id,
                    'partner_id': '',
                    'name': "Descuento por costo de venta  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                    'debit': 0.00,
                    'credit': monto_total,
                }),
            )

        registros_nomina_ids = self.env['registro.pagos.empleados'].search(
            [('company_id', '=', self.company_id.id),
             ('date', '>=', self.date_from), ('date', '<=', self.date_to), ('state', '=', '1')])
        for nomina in registros_nomina_ids:
            for line in nomina.pagos_ids:
                if line.ctta_analitica_id.code == '600023':
                    debit += line.monto_pago
                    journal_lines.append(
                        (0, 0, {
                            'account_id': line.account_id.id,
                            'partner_id': '',
                            'name': "Gasto por costo de venta  %s y pago de nómina %s" % (self.name, nomina.name),
                            'debit': line.monto_pago,
                            'credit': 0.00,
                        }),
                    )
        account_variacion_id = self.env['account.account'].search(
            [('code_alias', '=', '501010410'), ('company_id', '=', self.company_id.id)],
            limit=1)
        if not account_variacion_id:
            raise UserError('No existe el registro de la cuenta de variacion costo de venta con el código 501010410')
        if credit > debit:
            monto = credit - debit
            journal_lines.append(
                (0, 0, {
                    'account_id': account_variacion_id.id,
                    'partner_id': '',
                    'name': "Gasto por costo de venta  %s y pago de nómina %s" % (self.name, nomina.name),
                    'debit': monto,
                    'credit': 0.00,
                }),
            )
        if debit > credit:
            monto = debit - credit
            journal_lines.append(
                (0, 0, {
                    'account_id': account_variacion_id.id,
                    'partner_id': '',
                    'name': "Gasto por costo de venta  %s y pago de nómina %s" % (self.name, nomina.name),
                    'debit': 0.00,
                    'credit': monto,
                }),
            )
        busq_diario = self.bank_journal_id

        journal_item = self.env['account.move'].create({
            'ref': 'Pago coste de venta referente a %s por proyectos' % (self.name),
            'journal_id': busq_diario.id,
            'line_ids': journal_lines,
            'type': 'entry',
            'state': 'draft'
        })

        journal_item.action_post()
        self.movimiento_proyectos = journal_item
        self.state = '2'
        # descomentar esto
        # for nomina in registros_nomina_ids:
        #     nomina.state = '2'
        return


    def action_view_movimientos_ids(self):
        self.ensure_one()
        return {
            'name': self.movimiento_proyectos.name,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': self.movimiento_proyectos.id,
        }