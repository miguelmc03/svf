# -*- coding: utf-8 -*-

from odoo import models, fields, api


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
