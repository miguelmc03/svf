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
            vals_list.update({'product_add_mode': 'matrix'})
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
        if vals_list.get('checking_core') == 'si':
            product = self.env['product.template'].search([('name', '=', vals_list.get('name'))])
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', product.id)], limit=1)
            picking_type = self.env['stock.picking.type'].search([('sequence_code', '=', 'DVCC')])
            team = self.env['quality.alert.team'].search([('es_core', '=', 'si')])
            if not team:
                raise Warning(_('Por favor configure un equipo para core en el módulo de cálidad'))
            quality = self.env['quality.point.test_type'].search([('name', '=', 'Measure')])
            company_id = self.env['res.company'].search([('id', '=', '5')])
            vals = {
                'title': vals_list.get('name'),
                'product_tmpl_id': product.id,
                'product_id': product_id.id + 1,
                'picking_type_id': picking_type.id,
                'company_id': company_id.id,
                'measure_frequency_type': 'all',
                'test_type_id': quality.id,
                'norm': 1000,
                'norm_unit': 'MX',
                'tolerance_min': 1,
                'tolerance_max': 1000,
                'team_id': team.id,

            }
            listo = self.env['quality.point'].create(vals)
        return res

class SaleOrderInherit(models.Model):
    _inherit = "sale.order"

    refund_core = fields.Selection([('si', 'Si'), ('no', 'No')], default='no')

    def action_quotation_send(self):
        if self.refund_core == 'no':
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
        if self.refund_core == 'no':
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
        if vals.get('refund_core') == 'no':
            number_variants = 1
            last_product_id = None
            quantity = 0
            if vals.get('order_line'):
                for line in vals.get('order_line'):
                    if number_variants == 1:
                        if 'product_template_id' in line[2]:
                            id = line[2]['product_template_id']
                            product = self.env['product.template'].search([('id', '=', id)])
                            if product.checking_core == 'si':
                                number_variants = product.product_variant_count
                                last_product_id = line[2]['product_id']
                                quantity = line[2]['product_uom_qty']
                    else:
                        if 'product_template_id' in line[2]:
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

class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    @api.model
    def create(self, vals):
        number_variants = 1
        last_product_id = None
        quantity = 0
        if vals.get('order_line'):
            for line in vals.get('order_line'):
                if 'product_template_id' in line[2]:
                    if number_variants == 1:
                        id = line[2]['product_template_id']
                        product = self.env['product.template'].search([('id', '=', id)])
                        if product.checking_core == 'si':
                            number_variants = product.product_variant_count
                            last_product_id = line[2]['product_id']
                            if 'product_uom_qty' in line[2]:
                                quantity = line[2]['product_uom_qty']
                            else:
                                quantity = line[2]['product_qty']
                    else:
                        number_variants = number_variants - 1
                        id = line[2]['product_template_id']
                        product = self.env['product.template'].search([('id', '=', id)])
                        if not last_product_id in product.product_variant_ids.ids:
                            raise Warning(_('Falta el core del producto'))
                        if 'product_uom_qty' in line[2]:
                            if line[2]['product_uom_qty'] != quantity:
                                raise Warning(_('La cantidad de los cores no es igual a la del producto'))
                        else:
                            if line[2]['product_qty'] != quantity:
                                raise Warning(_('La cantidad de los cores no es igual a la del producto'))
            if number_variants != 1:
                raise Warning(_('Falta el Core del producto'))
        res = super(PurchaseOrderInherit, self).create(vals)
        return res

    def action_rfq_send(self):
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
        return super(PurchaseOrderInherit, self).action_rfq_send()

    def print_quotation(self):
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
        return super(PurchaseOrderInherit, self).print_quotation()

    def button_confirm(self):
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
        return super(PurchaseOrderInherit, self).button_confirm()

class QualityAlertTeamInherit(models.Model):
    _inherit ='quality.alert.team'

    es_core = fields.Selection([('si', 'Si'), ('no', 'No')], required=True)
