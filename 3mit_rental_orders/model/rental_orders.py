# coding: utf-8
from odoo import fields, exceptions, models

class addField(models.Model):
    _inherit = 'product.template'
    rental_account_id = fields.Many2one("account.account", string="Cuentas")

class createInvoice(models.Model):
    _inherit = 'account.move.line'

    def _get_computed_account(self):
        # Orden de venta/alquiler activa
        sale_order_obj = self.env['sale.order']
        sale_order = sale_order_obj.browse(self._context['active_id'])

        # Si es un pedido de alquiler
        if sale_order.is_rental_order == True:
            for line in sale_order.order_line:
                # Se reemplaza la cuenta de ingreso predeterminada por la cuenta seleccionada
                line.product_template_id.property_account_income_id = line.product_template_id.rental_account_id

            return super(createInvoice, self)._get_computed_account()
        # Si es un pedido de venta
        else:
            return super(createInvoice, self)._get_computed_account()
