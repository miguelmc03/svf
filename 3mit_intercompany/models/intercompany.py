from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.http import request
from odoo.tests import Form, tagged
class CompanyEdit(models.Model):
    _inherit = "res.company"
    inter_automatic = fields.Boolean(default=False)
    
class purchase_order(models.Model):
    _inherit = "purchase.order"
    state_auto = fields.Boolean(default=False)


    @api.model
    def create(self, vals):
        res = super(purchase_order, self).create(vals)
        if res.company_id.inter_automatic == True:
            res.state_auto = True
        return res

    def automatizar(self):
        self.state_auto = False
        self.button_confirm()
        return

class stock_edit(models.Model):
    _inherit = "stock.picking"

    @api.model
    def create(self, vals):
        res = super(stock_edit, self).create(vals)
        if res.company_id.inter_automatic == True:
            orden = self.env['purchase.order'].search([('state_auto', '=', True)], order='id desc', limit=1)
            if orden:
                orden.automatizar()
        return res
    
    def button_validate(self):
        res = super(stock_edit, self).button_validate()
        company_id_uno = self.company_id
        company_id_dos = self.env['res.company'].search([('partner_id', '=', self.partner_id.id)], order='id desc', limit=1)
        if company_id_dos.inter_automatic == True:
            orden_venta = request.env['sale.order'].search([('client_order_ref', '=', self.origin), ('partner_id', '=', company_id_uno.partner_id.id), ('company_id', '=', company_id_dos.id)])
            orden_compra = request.env['purchase.order'].search([('origin', '=', orden_venta.name), ('company_id', '=', company_id_dos.id)], order='id desc', limit=1)
            #valido la recepcion de la orden de compras
            for pick in orden_compra.picking_ids:
                pick_id = request.env['stock.picking'].search([('id', '=', pick.id), ('company_id', '=', company_id_dos.id)], order='id desc', limit=1)
                for line in pick_id.move_ids_without_package:
                    line.quantity_done = line.product_uom_qty
                pick_id.button_validate()
            #valido el despacho de la orden de ventas
            for pick in orden_venta.picking_ids:
                pick_id = request.env['stock.picking'].search([('id', '=', pick.id), ('company_id', '=', company_id_dos.id)], order='id desc', limit=1)
                for line in pick_id.move_ids_without_package:
                    line.quantity_done = line.product_uom_qty
                    line.reserved_availability = line.product_uom_qty
                pick_id.button_validate()
            #proceso de crear factura de orden de compra
            action = orden_compra.action_view_invoice()
            vb = Form(request.env['account.move'].with_context(action['context']))
            vb = vb.save()
            vb.post()
            #crear la factura y procesar de venta
            action = orden_venta._create_invoices()
            action.post()
        return res