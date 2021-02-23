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
import datetime

class RegistroDePosVentaLines(models.Model):
    _name = 'pagos.diferidos.lines'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    pagos_id = fields.Many2one('registro.pagos.diferidos', 'pagos diferidos relacion', ondelete='cascade', index=True)
    proyecto_id = fields.Many2one('project.project', string='Proyecto', required=True, readonly=True)
    marca_id = fields.Many2one('marcas.model', string='Marca', required=True, readonly=True)
    horas = fields.Float(string="Horas")
    monto = fields.Float(string="Monto horas")
    date = fields.Date('Date', default=date.today())
    valor_pago = fields.Float(string="Monto a diferir")
    aviso = fields.Boolean(default=False)
    acumulado = fields.Float(string="Monto a diferir anteriores")
    total_gastos = fields.Float(string="Monto gastos")

class RegistroDePagosPosVenta(models.Model):
    
    _name = 'registro.pagos.diferidos'
    
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

    @api.model
    def year_selection(self):
        year = 2018  # año de inicio
        year_list = []
        while year != 2500:  # año fin
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    year = fields.Selection(
        year_selection,
        string="Year",
        default="2021",  # as a default value it would be 2019
    )
    mes = fields.Selection([
        ('01', 'Enero'),
        ('02', 'Febrero'),
        ('03', 'Marzo'),
        ('04', 'Abril'),
        ('05', 'Mayo'),
        ('06', 'Junio'),
        ('07', 'Julio'),
        ('08', 'Agosto'),
        ('09', 'Septiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre')
    ])
    date = fields.Date('Date')

    #date_from = fields.Date(string='fecha busqueda', required=True)

    company_id = fields.Many2one('res.company', string='Compañia', required=True, readonly=True,
                                 default=lambda self: self.env.company)
   
    pagos_ids = fields.One2many('pagos.diferidos.lines', 'pagos_id')
    bank_journal_id = fields.Many2one('account.journal', string='Diario del banco',
                                      check_company=True,
                                      domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
                                      default=_default_bank_journal_id,
                                      help="Diario de diferidos a marcas.")

    movimiento_proyectos = fields.Many2one('account.move', readonly=True, string="Movimiento contable diferidos")
    porcentaje = fields.Float('porcentaje diferido')
    condicional_revert = fields.Boolean(default=False)
    movimiento_revert = fields.Many2one('account.move', readonly=True, string="Movimiento contable diferidos revertidos")

    @api.onchange('mes', 'year')
    def _onchange_mes(self):
        if self.mes:
            self.date = datetime.datetime(int(self.year), int(self.mes), 1) - timedelta(days=1)
        return

    def action_confirm(self):
        if self.porcentaje <= 0:
            raise UserError(
                'Ingrese un monto valido para la tarifa de mano de obra para el calculo de ingreso diferido.')
        date_from = datetime.datetime(int(self.year), int(self.mes), 1)
        date_to = datetime.datetime(int(self.year), int(self.mes) + 1, 1) - timedelta(days=1)
        self.date = datetime.datetime(int(self.year), int(self.mes), 1) - timedelta(days=1)
        costo_venta_id = self.env['registro.pagos.posventa'].search([('company_id', '=', self.company_id.id),
                 ('date', '>=', date_from), ('date', '<=', date_to), ('state', '=', '2')], order='id desc', limit=1)
        diferidos_lines = []
        if not costo_venta_id:
            raise UserError(
                'No existe un registro de costo de venta para el mes seleccionado.')
        for lin in costo_venta_id.pagos_ids:
            if lin.proyecto_id.sale_order_id and lin.proyecto_id.sale_order_id.invoice_ids:
                aviso = True
            else:
                aviso = False
            acumulado = 0
            pagos_diferidos_ids = self.env['pagos.diferidos.lines'].search([('company_id', '=', self.company_id.id),
                                                                            ('proyecto_id', '=', lin.proyecto_id.id), ('pagos_id.state', '=', '2')])
            for dif in pagos_diferidos_ids:
                acumulado += dif.valor_pago
            diferidos_lines.append(
                (0, 0, {
                    'name': 'Pagos diferidos: ' + self.name,
                    'proyecto_id': lin.proyecto_id.id,
                    'marca_id': lin.marca_id.id,
                    'date': self.date,
                    'monto': lin.monto,
                    'horas': lin.horas,
                    'pagos_id': self.id,
                    'valor_pago': (lin.horas * self.porcentaje) + lin.total_gastos,
                    'aviso': aviso,
                    'acumulado': acumulado,
                    'total_gastos': lin.total_gastos,
                })
            )
        self.write({'pagos_ids': diferidos_lines})

        self.state = '1'

        return



    def action_asignar(self):
        journal_lines = []
        for pro in self.pagos_ids:
            if pro.aviso == False:
                monto_total = pro.monto
                if not pro.marca_id.account_ingresos_id:
                    raise UserError(
                        'La marca %s no tiene una cuenta de ingresos diferidos registrada' %(pro.marca_id.name))
                account_first = pro.marca_id.account_ingresos_id

                journal_lines.append(
                    (0, 0, {
                        'account_id': account_first.id,
                        'partner_id': '',
                        'name': "Diferido por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                        'debit': 0.00,
                        'credit': monto_total,
                    }),
                )
                account_variacion_id = self.env['account.account'].search(
                    [('code_alias', '=', '201060104'), ('company_id', '=', self.company_id.id)],
                    limit=1)
                if not account_variacion_id:
                    raise UserError(
                        'No existe el registro de la cuenta de Crédito Diferido Servicio con el código 201060104')

                journal_lines.append(
                    (0, 0, {
                        'account_id': account_variacion_id.id,
                        'partner_id': '',
                        'name': "Diferido por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                        'debit': monto_total,
                        'credit': 0.00,
                    }),
                )

                #///////////////////////////////////////////MONTOS ACUMULADOS/////////////////////////
                if pro.acumulado > 0:
                    monto_total_acumulado = pro.acumulado
                    journal_lines.append(
                        (0, 0, {
                            'account_id': account_first.id,
                            'partner_id': '',
                            'name': "Diferido acumulado por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                            'debit': 0.00,
                            'credit': monto_total_acumulado,
                        }),
                    )

                    journal_lines.append(
                        (0, 0, {
                            'account_id': account_variacion_id.id,
                            'partner_id': '',
                            'name': "Diferido acumulado por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                            'debit': monto_total_acumulado,
                            'credit': 0.00,
                        }),
                    )

        busq_diario = self.bank_journal_id

        journal_item = self.env['account.move'].create({
            'ref': 'Ingreso diferido servicio por %s por proyectos' % (self.name),
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
            'name': self.movimiento_proyectos.name,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': self.movimiento_proyectos.id,
        }

    def action_view_movimientos_diferidos_ids(self):
        self.ensure_one()
        return {
            'name': self.movimiento_revert.name,
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'res_id': self.movimiento_revert.id,
        }

    def action_revertir(self):
        registros_diferidos_ids = self.env['registro.pagos.diferidos'].search([
            ('state', '=', '2'), ('condicional_revert', '!=', True)])
        for reg in registros_diferidos_ids:
            reg.action_revertir_ejecute()
    def action_revertir_ejecute(self):
        if (self.condicional_revert != True) and (self.state == '2'):
            if self.mes == '12':
                return
            journal_lines = []
            for pro in self.pagos_ids:
                if pro.aviso == False:
                    monto_total = pro.monto
                    if not pro.marca_id.account_ingresos_id:
                        raise UserError(
                            'La marca %s no tiene una cuenta de ingresos diferidos registrada' %(pro.marca_id.name))
                    account_first = pro.marca_id.account_ingresos_id
                    account_variacion_id = self.env['account.account'].search(
                        [('code_alias', '=', '201060104'), ('company_id', '=', self.company_id.id)],
                        limit=1)
                    if not account_variacion_id:
                        raise UserError(
                            'No existe el registro de la cuenta de Crédito Diferido Servicio con el código 201060104')

                    journal_lines.append(
                        (0, 0, {
                            'account_id': account_variacion_id.id,
                            'partner_id': '',
                            'name': "Diferido REVERTIDO por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                            'debit': monto_total,
                            'credit': 0.00,
                        }),
                    )

                    journal_lines.append(
                        (0, 0, {
                            'account_id': account_first.id,
                            'partner_id': '',
                            'name': "Diferido REVERTIDO por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                            'debit': 0.00,
                            'credit': monto_total,
                        }),
                    )

                    #///////////////////////////////////////////MONTOS ACUMULADOS/////////////////////////
                    if pro.acumulado > 0:
                        monto_total_acumulado = pro.acumulado
                        journal_lines.append(
                            (0, 0, {
                                'account_id': account_variacion_id.id,
                                'partner_id': '',
                                'name': "Diferido REVERTIDO acumulado por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                                'debit': monto_total_acumulado,
                                'credit': 0.00,
                            }),
                        )

                        journal_lines.append(
                            (0, 0, {
                                'account_id': account_first.id,
                                'partner_id': '',
                                'name': "Diferido REVERTIDO acumulado por concepto  %s y proyecto %s" % (self.name, pro.proyecto_id.name),
                                'debit': 0.00,
                                'credit': monto_total_acumulado,
                            }),
                        )

            busq_diario = self.bank_journal_id

            journal_item = self.env['account.move'].create({
                'ref': 'Ingreso diferido REVERTIDO por servicio a %s por proyectos' % (self.name),
                'journal_id': busq_diario.id,
                'line_ids': journal_lines,
                'type': 'entry',
                'state': 'draft'
            })

            journal_item.action_post()
            self.movimiento_revert = journal_item
            self.condicional_revert = True
        return