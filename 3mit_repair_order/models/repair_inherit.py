# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RepairOrderInherit(models.Model):
    _inherit = 'repair.order'

    analytic_account_id = fields.Many2one(string="Cuenta analítica asociada",
                                          related="ticket_id.team_id.project_id.analytic_account_id")

    def action_validate(self):
        res = super(RepairOrderInherit, self).action_validate()
        repair_vals = {
            'name': self.name + ' - ' + self.ticket_id.name,
            'account_id': self.analytic_account_id.id,
            'date': self.create_date,
            'amount': self.amount_total * -1,
        }

        analytic_account_line = self.env['account.analytic.line']. \
            search([('account_id', '=', self.analytic_account_id.id)]).create(repair_vals)

        return res


class RepairLineInherit(models.Model):
    _inherit = 'repair.line'

    @api.onchange('type', 'repair_id')
    def onchange_operation_type(self):
        if not self.type:
            self.location_id = False
            self.location_dest_id = False
        elif self.type == 'add':
            self.onchange_product_id()
            args = self.repair_id.company_id and [('company_id', '=', self.repair_id.company_id.id)] or []
            warehouse = self.env['stock.warehouse'].search(args, limit=1)
            self.location_id = warehouse.lot_stock_id
            self.location_dest_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
        else:
            self.location_id = self.env['stock.location'].search([('usage', '=', 'production')], limit=1).id
            self.location_dest_id = self.env['stock.location'].search([('scrap_location', '=', True)], limit=1).id

    # LÓGICA PARA TOMAR EL PRECIO POR UNIDAD DEL PRODUCTO Y REALIZA BYPASS INDEPENDIENTEMENTE DE SI ES TYPE REMOVE O NO:
    @api.onchange('product_uom')
    def _onchange_product_uom(self):
        partner = self.repair_id.partner_id
        pricelist = self.repair_id.pricelist_id
        if pricelist and self.product_id and self.type:
            price = pricelist.get_product_price(self.product_id, self.product_uom_qty, partner,
                                                uom_id=self.product_uom.id)
            if price is False:
                warning = {
                    'title': _('No se encontró una línea de lista de precios válida.'),
                    'message':
                        _(
                            "No se pudo encontrar una línea de lista de precios que coincida con este producto y "
                            "la cantidad. \nDebe cambiar el producto, la cantidad o la lista de precios.")}
                return {'warning': warning}
            else:
                self.price_unit = price

    # LÓGICA PARA TOMAR EL COSTE DEL PRODUCTO
    # @api.onchange('product_uom')
    # def _onchange_product_uom(self):
        # price = self.product_id.standard_price
        # if price is False:
            # warning = {
                # 'title': _('No se encontró una línea de lista de precios válida.'),
                # 'message':
                    # _(
                        # "No se pudo encontrar una línea de lista de precios que coincida con este producto y "
                        # "la cantidad. \nDebe cambiar el producto, la cantidad o la lista de precios.")}
            # return {'warning': warning}
        # else:
            # self.price_unit = price
