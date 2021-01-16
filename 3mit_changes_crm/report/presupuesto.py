# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, exceptions, fields
from odoo.exceptions import UserError, Warning
from datetime import datetime, date, timedelta

class ReportSimpleQuotation(models.AbstractModel):
    _name = 'report.3mit_changes_crm.template_sale_simple_order'

    @api.model
    def _get_report_values(self, docids, data):
        var = data
        slip_id = self.env['sale.simple.order'].search([('id','=',docids[0])])
        cliente_nombre = slip_id.partner_id if slip_id.partner_id else slip_id.partner_name
        fecha_presupuesto = datetime.strptime(str(slip_id.date_order.date()), '%Y-%m-%d')
        fecha_presupuesto = fecha_presupuesto.strftime('%d/%m/%Y')
        expiracion = datetime.strptime(str(slip_id.validity_date), '%Y-%m-%d')
        expiracion = expiracion.strftime('%d/%m/%Y')
        salesperson = slip_id.user_id.name
        docs = []
        lineas=[]
        for a in slip_id.order_line:
            lineas.append({
                    'nombre': a.name,
                    'cantidad': a.product_uom_qty,
                    'unidad': a.product_uom.name,
                    'precio': self.separador_cifra(a.price_unit),
                    'impuestos': a.tax_id.amount,
                    'monto': self.separador_cifra(a.price_subtotal),
                })

        docs.append({
            'cliente_nombre':cliente_nombre,
            'fecha_presupuesto': fecha_presupuesto,
            'expiracion': expiracion,
            'salesperson': salesperson,
        })
        return {
            'model': self.env['report.3mit_changes_crm.template_sale_simple_order'],
            'docs': docs,
            'lineas':lineas,
            'total' : self.separador_cifra(slip_id.amount_total),
        }

    def separador_cifra(self,valor):
        monto = '{0:,.2f}'.format(valor).replace('.', '-')
        monto = monto.replace(',', '.')
        monto = monto.replace('-', ',')
        return  monto

