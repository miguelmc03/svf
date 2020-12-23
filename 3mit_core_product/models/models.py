# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions,_
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError
from odoo.exceptions import Warning

class CoreProduct(models.Model):
    _inherit = "product.template"

    check_core = fields.Boolean(string="Posee Core", default=False, store=True)
    checking_core = fields.Selection([('si', 'Si'), ('no', 'No')])

    @api.onchange('checking_core')
    def tiene_core(self):
        if self.checking_core == 'si':
            self.check_core = True
        else:
            self.check_core = False

    @api.model
    def create(self, vals_list):
        if vals_list.get('checking_core') == 'si':
            vals = {
                'name': vals_list.get('name'),
                'display_type': 'select',
                'create_variant': 'always',
                'value_ids': [
                (0, 0, {
                    'name': vals_list.get('name'),
                }),
                (0, 0, {
                    'name': 'C'+vals_list.get('name'),
                }),
            ],}
            move_obj = self.env['product.attribute'].create(vals)
            vals_list.update({'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': move_obj.id,
                    'value_ids': move_obj.value_ids
                }),
            ]})
        res = super(CoreProduct, self).create(vals_list)
        return res

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    def action_quotation_send(self):
        number_variants = 1
        last_product_id = None
        quantity = 0
        if self.order_line:
            for line in self.order_line:
                if number_variants == 1:
                    product = line.product_id
                    if product.checking_core == 'si':
                        number_variants = product.product_variant_count
                        last_product_id = product
                        quantity = line.product_uom_qty
                else:
                    number_variants = number_variants - 1
                    if not last_product_id in line.product_id.product_variant_ids:
                        raise Warning(_('Falta el core del producto'))
                    if line.product_uom_qty != quantity:
                        raise Warning(_('La cantidad de los cores no es igual a la del producto'))
            if number_variants != 1:
                raise Warning(_('Falta el Core del producto'))
        return super(SaleOrderInherit, self).action_quotation_send()

    def action_confirm(self):
        number_variants = 1
        last_product_id = None
        quantity = 0
        if self.order_line:
            for line in self.order_line:
                if number_variants == 1:
                    product = line.product_id
                    if product.checking_core == 'si':
                        number_variants = product.product_variant_count
                        last_product_id = product
                        quantity = line.product_uom_qty
                else:
                    number_variants = number_variants - 1
                    if not last_product_id in line.product_id.product_variant_ids:
                        raise Warning(_('Falta el core del producto'))
                    if line.product_uom_qty != quantity:
                        raise Warning(_('La cantidad de los cores no es igual a la del producto'))
            if number_variants != 1:
                raise Warning(_('Falta el Core del producto'))
        return super(SaleOrderInherit, self).action_confirm()

    @api.model
    def create(self, vals):
        number_variants = 1
        last_product_id = None
        quantity = 0
        if vals.get('order_line'):
            for line in vals.get('order_line'):
                if number_variants == 1:
                    id = line[2]['product_template_id']
                    product = self.env['product.template'].search([('id', '=', id)])
                    if product.checking_core == 'si':
                        number_variants = product.product_variant_count
                        last_product_id = line[2]['product_id']
                        quantity = line[2]['product_uom_qty']
                else:
                    number_variants = number_variants - 1
                    id = line[2]['product_template_id']
                    product = self.env['product.template'].search([('id', '=', id)])
                    if not last_product_id in product.product_variant_ids.ids:
                        raise Warning(_('Falta el core del producto'))
                    if line[2]['product_uom_qty'] != quantity:
                        raise Warning(_('La cantidad de los cores no es igual a la del producto'))
            if number_variants != 1:
                raise Warning(_('Falta el Core del producto'))
        res = super(SaleOrderInherit, self).create(vals)
        return res