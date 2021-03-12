# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from datetime import date
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError, Warning

class SettingUpCore(models.Model):
    _name = "core.settings"

    name = fields.Char()
    account = fields.Many2one('account.account', 'Cuenta')

class PickingTypeInherit(models.Model):
    _inherit = "stock.picking.type"

    es_core = fields.Selection([('si', 'Si'), ('no', 'No')], default='no')
    account_debit_id = fields.Many2one('account.account', 'Cuenta a Debitar')
    account_credit_id = fields.Many2one('account.account', 'Cuenta a Acreditar')
    journal_advanced_id = fields.Many2one('account.journal', 'Diario de Anticipos')

class PickingInherit(models.Model):
    _inherit = "stock.picking"
    refund_flag = fields.Boolean()
    code = fields.Char()
    valoracion_ids = fields.One2many('valoracion.line', 'stok_picking_id', 'Valoracion', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Factura Asociada')
    associated_stock_id = fields.Many2one('stock.picking', string='Transferencia de Devolución' )
    es_devuelto = fields.Selection([('si', 'Si'), ('no', 'No')], default='no')
    @api.onchange('picking_type_id')
    def reload_refund_flag(self):
        if self.picking_type_id:
            self.code = self.picking_type_id.sequence_code
            if self.picking_type_id.es_core == 'si':
                self.refund_flag = True
            else:
                self.refund_flag = False

    def write(self, vals):
        if self.picking_type_id.es_core == 'si':
            if not vals.get('refund_flag', False):
                vals.update({'refund_flag': True})
        if not self.valoracion_ids:
            if not vals.get('valoracion_ids', False):
                valoracion = []
                for line in self.associated_stock_id.valoracion_ids:
                    valoracion.append(
                        (0, 0, {
                            'stok_picking_id': self.id,
                            'product_id': line.product_id.id,
                            'amount': line.amount,
                        }))
                if not vals.get('valoracion_ids', False):
                    vals.update({'valoracion_ids': valoracion})
        res = super(PickingInherit, self).write(vals)
        return res


    @api.onchange('associated_stock_id')
    def reload_lines_and_valoration(self):
        if self.associated_stock_id:
            move = []
            for line in self.associated_stock_id.move_ids_without_package:
                vals = {
                        'product_id': line.product_id.id,
                        'product_uom_qty': line.product_uom_qty,
                        'picking_id': self.id,
                        'name': line.name,
                        'product_uom' : line.product_uom.id,
                        'location_id' : self.location_id.id,
                        'location_dest_id' : self.location_dest_id.id,

                    }
                move_obj = self.env['stock.move'].create(vals)
                move.append(move_obj.id)
            self.move_ids_without_package = move

    def automatic_book_entry(self):
        company_id = self.env['res.company'].search([('id', '=', 1)])
        account_debit_id = self.env['core.settings'].search([('name', '=', 'cxc_mtu')]).account.id
        account_credit_id = self.env['core.settings'].search([('name', '=', 'cxp_ops')]).account.id
        journal_id = request.env['account.journal'].search([('devolucion_core', '=', 'si'), ('company_id', '=', company_id.id)])
        if not journal_id:
            raise Warning(_('Valla a los Diarios de la NV y seleccione el diario de devolución correspondiente'))
        monto = 0
        for line in self.valoracion_ids:
            monto = monto + line.amount
        vals = {
            # 'name': name,
            'date': self.date,
            'journal_id': journal_id.id,
            'line_ids': False,
            'state': 'draft',
        }
        move_obj = request.env['account.move'].with_context(force_company=company_id.id)
        move_id = move_obj.create(vals)

        self.move_advance_ = {
            'account_id': account_credit_id,
            'company_id': self.company_id.id,
            'date_maturity': False,
            'date': self.date,
            'partner_id': self.partner_id.id,
            'move_id': move_id.id,
            'name': self.name,
            'journal_id': journal_id.id,
            'credit': monto,
            'debit': 0.0,
        }
        asiento = self.move_advance_
        move_line_obj = request.env['account.move.line']
        move_line_id1 = move_line_obj.with_context(check_move_validity=False).create(asiento)

        asiento['account_id'] = account_debit_id
        asiento['credit'] = 0.0
        asiento['debit'] = monto

        move_line_id2 = move_line_obj.create(asiento)
        move_id.action_post()

    def action_confirm(self):
        res = super(PickingInherit, self).action_confirm()
        if self.refund_flag:
            increase = []
            [increase.append(
                (0, 0, {
                    'product_id': product.product_id.id,
                    'amount': product.product_id.standard_price,
                })
            ) for product in self.move_ids_without_package]
            self.write({'valoracion_ids': increase})
        return res

    # @api.onchange('move_ids_without_package')
    # def update_valoration_items(self):
    #     if self.move_ids_without_package:
    #         increase = []
    #         for product_line in self:
    #             [increase.append(
    #                 (0, 0, {
    #                     'product_id': product.product_id.id,
    #                     'amount': 0,
    #                 })
    #             ) for product in product_line.move_ids_without_package]
    #         self.write({'valoracion_ids': increase})

class ValoracionLine(models.Model):
    _name = "valoracion.line"

    stok_picking_id = fields.Many2one(comodel_name="stock.picking", string="Transferencia")
    product_id = fields.Many2one('product.product', 'Producto', readonly=True)
    amount = fields.Monetary(string="Monto Pieza", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id)

class QualityCheckInherit(models.Model):
    _inherit = "quality.check"

    def do_measure(self):
        res = super(QualityCheckInherit, self).do_measure()
        # if not self.picking_id.valoracion_ids:
        #     increase = []
        #     for product_line in self.picking_id:
        #         [increase.append(
        #             (0, 0, {
        #                 'product_id': product.product_id.id,
        #                 'amount': 0,
        #                    })
        #           ) for product in product_line.move_ids_without_package]
        #     self.picking_id.write({'valoracion_ids': increase})
        # for line in self.picking_id.valoracion_ids:
        #     if line.product_id == self.product_id:
        #         line.amount = self.measure

class StockMoveInherit(models.Model):
    _inherit = "stock.move"

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
        """
        Generate the account.move.line values to post to track the stock valuation difference due to the
        processing of the given quant.
        """
        self.ensure_one()
        if self.picking_id.refund_flag:
            final_cost = 0
            for product in self.picking_id.valoracion_ids:
                if self.product_id == product.product_id:
                    for line in self.picking_id.move_ids_without_package:
                        if line.product_id == product.product_id:
                            final_cost = (final_cost + product.amount)*line.product_uom_qty
            # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
            # the company currency... so we need to use round() before creating the accounting entries.
            debit_value = self.company_id.currency_id.round(final_cost)
            credit_value = debit_value

            valuation_partner_id = self._get_partner_id_for_valuation_lines()
            res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]
            return res
        else:
            res = super(StockMoveInherit, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
            return res

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        # This method returns a dictionary to provide an easy extension hook to modify the valuation lines (see purchase for an example)
        self.ensure_one()
        if self.picking_id.refund_flag:
            debit_line_vals = {
                'name': description,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'debit': debit_value if debit_value > 0 else 0,
                'credit': -debit_value if debit_value < 0 else 0,
                'account_id': debit_account_id,
            }

            credit_line_vals = {
                'name': description,
                'product_id': self.product_id.id,
                'quantity': qty,
                'product_uom_id': self.product_id.uom_id.id,
                'ref': description,
                'partner_id': partner_id,
                'credit': credit_value if credit_value > 0 else 0,
                'debit': -credit_value if credit_value < 0 else 0,
                'account_id': credit_account_id,
            }

            rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}

            return rslt
        else:
            res = super(StockMoveInherit, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
            return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        if self.picking_id.refund_flag:
            # journal_id = self.picking_id.picking_type_id.journal_advanced_id
            # credit_account_id = self.picking_id.picking_type_id.account_credit_id
            # debit_account_id = self.picking_id.picking_type_id.account_debit_id
            AccountMove = self.env['account.move']

            move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
            if move_lines:
                date = self._context.get('force_period_date', fields.Date.context_today(self))
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': date,
                    'ref': description,
                    'stock_move_id': self.id,
                    'stock_valuation_layer_ids': [(6, None, [svl_id])],
                    'type': 'entry',
                })
                new_account_move.post()
        else:
            res = super(StockMoveInherit, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)
            return res
    def _get_accounting_data_for_valuation(self):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        if self.picking_id.refund_flag:
            acc_dest = self.picking_id.picking_type_id.account_credit_id.id
            acc_src = self.picking_id.picking_type_id.account_credit_id.id
            acc_valuation = self.picking_id.picking_type_id.account_debit_id.id
            journal_id = self.picking_id.picking_type_id.journal_advanced_id.id
            return journal_id, acc_src, acc_dest, acc_valuation
        else:
            res = super(StockMoveInherit, self)._get_accounting_data_for_valuation()
            return res

class AccountMoveReversalInherit(models.TransientModel):
    """
    Account move reversal wizard, it cancel an account move by reversing it.
    """
    _inherit = 'account.move.reversal'

    is_core = fields.Boolean(default=False)
    es_devolucion = fields.Boolean(default=False)

    def reverse_moves(self):
        moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get(
            'active_model') == 'account.move' else self.move_id
        moves.is_core = self.is_core
        moves.es_devolucion = self.es_devolucion
        res = super(AccountMoveReversalInherit, self).reverse_moves()
        return res

class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    is_core = fields.Boolean(default=False)
    es_devolucion = fields.Boolean(default=False)
    # retorno_fabrica = fields.Selection([('si', 'Si'), ('no', 'No')], string="Retorno de Core a Fabrica")

    def action_post(self):
        res = super(AccountMoveInherit, self).action_post()
        if self.es_devolucion:
            # self.retorno_fabrica = 'no'
            self.automatic_book_entry()
        
        
        return res

    def automatic_book_entry(self):
        company_id = self.env['res.company'].search([('id', '=', 1)])
        account_debit_id = self.env['core.settings'].search([('name', '=', 'cxc_mtu')]).account.id
        account_credit_id = self.env['core.settings'].search([('name', '=', 'cxp_ops')]).account.id
        journal_id = request.env['account.journal'].search(
            [('devolucion_core', '=', 'si'), ('company_id', '=', company_id.id)])
        if not journal_id:
            raise Warning(_('Valla a los Diarios de la NV y seleccione el diario de devolución correspondiente'))
        monto = 0
        for line in self.invoice_line_ids:
            monto = monto + line.price_subtotal
        if self.currency_id.id == self.env.company.currency_id.id:
            currency_rate = self.env['res.currency.rate'].search([
                ('currency_id', '=', self.env.company.currency_id.id),
                ('name', '=', date.today()),
            ]).rate
            if not currency_rate:
                raise Warning(_('Ingrese una tasa para la fecha de hoy en el sistema'))
            monto = monto / currency_rate
        vals = {
            # 'name': name,
            'date': self.date,
            'journal_id': journal_id.id,
            'line_ids': False,
            'state': 'draft',
        }
        move_obj = request.env['account.move'].with_context(force_company=company_id.id)
        move_id = move_obj.create(vals)

        self.move_advance_ = {
            'account_id': account_debit_id,
            'company_id': self.company_id.id,
            'date_maturity': False,
            'date': self.date,
            'partner_id': self.partner_id.id,
            'move_id': move_id.id,
            'name': self.name,
            'journal_id': journal_id.id,
            'credit': monto,
            'debit': 0.0,
        }
        asiento = self.move_advance_
        move_line_obj = request.env['account.move.line']
        move_line_id1 = move_line_obj.with_context(check_move_validity=False).create(asiento)

        asiento['account_id'] = account_credit_id
        asiento['credit'] = 0.0
        asiento['debit'] = monto

        move_line_id2 = move_line_obj.create(asiento)
        move_id.action_post()


    def _reverse_move_vals(self, default_values, cancel=True):
        ''' Reverse values passed as parameter being the copied values of the original journal entry.
        For example, debit / credit must be switched. The tax lines must be edited in case of refunds.

        :param default_values:  A copy_date of the original journal entry.
        :param cancel:          A flag indicating the reverse is made to cancel the original journal entry.
        :return:                The updated default_values.
        '''
        self.ensure_one()

        def compute_tax_repartition_lines_mapping(move_vals):
            ''' Computes and returns a mapping between the current repartition lines to the new expected one.
            :param move_vals:   The newly created invoice as a python dictionary to be passed to the 'create' method.
            :return:            A map invoice_repartition_line => refund_repartition_line.
            '''
            # invoice_repartition_line => refund_repartition_line
            mapping = {}

            # Do nothing if the move is not a credit note.
            if move_vals['type'] not in ('out_refund', 'in_refund'):
                return mapping
            if self.es_devolucion:
                change = []
                importe = []
                # self.retorno_fabrica = 'no'
                move_vals.update({
                            'type': 'in_refund',
                        })
                account_credit = self.env['core.settings'].search([('name', '=', 'ingreso_core')]).account.id
                account_debit = self.env['core.settings'].search([('name', '=', 'cxp_nv')]).account.id
                for line_command in move_vals.get('line_ids', []):
                    line_vals = line_command[2]
                    if line_vals.get('debit'):
                        change.append(0)
                        change.append(line_vals.get('price_subtotal'))
                        change.append(line_vals.get('price_total'))
                        change.append(line_vals.get('debit'))
                        line_vals.update({
                            'account_id': account_debit,
                        })
                        change.append(line_vals.get('price_unit'))
                        change.append(line_vals.get('account_id'))
                        # if line_vals.get('amount_currency'):
                        #     importe.append(line_vals.get('amount_currency'))

                    if line_vals.get('credit'):
                        change.append(1)
                        change.append(line_vals.get('price_subtotal'))
                        change.append(line_vals.get('price_total'))
                        change.append(line_vals.get('credit'))
                        line_vals.update({
                            'account_id': account_credit,
                        })
                        change.append(line_vals.get('price_unit'))
                        change.append(line_vals.get('account_id'))
                        # if line_vals.get('amount_currency'):
                        #     importe.append(line_vals.get('amount_currency'))

                j = len(importe)-1
                i = 0
                for line_command in move_vals.get('line_ids', []):
                    line_vals = line_command[2]
                    if change[i] == 0:
                        line_vals.update({
                            'account_id': change[i+5],
                            'price_unit': change[i+4],
                            'credit': change[i+3],
                            'price_total': change[i +2],
                            'price_subtotal': change[i +1],
                            'debit': 0,
                            'amount_currency':  -line_vals.get('amount_currency'),
                        })
                        # if j > -1:
                        #     line_vals.update({
                        #         'amount_currency': importe[j] if importe[j] else 0,
                        #     })
                    elif change[i] == 1:
                        line_vals.update({
                            'account_id': change[i+5],
                            'price_unit': change[i+4],
                            'debit': change[i+3],
                            'price_total': change[i +2],
                            'price_subtotal': change[i+1],
                            'credit': 0,
                            'amount_currency':  -line_vals.get('amount_currency'),
                        })
                        # if j > -1:
                        #     line_vals.update({
                        #         'amount_currency': importe[j] if importe[j] else 0,
                        #     })
                    i = i+6
                    j = j-1
            if self.is_core:
                # diff= 0
                # num = 0
                # count = 0
                # flag = 0
                # value = 0
                for line_command in move_vals.get('line_ids', []):
                    line_vals = line_command[2]  # (0, 0, {...})
                    product = self.env['product.product'].search([('id', '=', line_vals.get('product_id'))])
                    id=product.product_tmpl_id.id
                    product = self.env['product.template'].search([('id', '=', id )])
                    account = product.categ_id.property_account_income_categ_id.id
                    # stock = self.env['stock.picking'].search([('invoice_id', '=', self.id)], order='date desc', limit=1)
                    # if flag:
                    #     count += 1
                        # value = value + line_vals.get('credit')
                    # for line in stock.valoracion_ids:
                    #     if num == 1:
                    #         if line_vals.get('debit'):
                    #             line_vals.update({
                    #                 'debit': line_vals.get('debit')-diff,
                    #             })
                    #             num = 0
                    #             flag = 1
                    if line_vals.get('account_id') == account:
                        account_id= self.env['core.settings'].search([('name', '=', 'Nota_Credito')]).account.id
                        line_vals.update({
                            'account_id': account_id,
                        })

                        # for line in stock.valoracion_ids:
                        #     if line.product_id.id == line_vals.get('product_id'):
                        #         diff = diff + (line_vals.get('credit')-line.amount)
                        #         line_vals.update({
                        #             'credit': line.amount,
                        #         })
                        #         num = 1
            for line_command in move_vals.get('line_ids', []):
                line_vals = line_command[2]  # (0, 0, {...})

                if line_vals.get('tax_line_id'):
                    # Tax line.
                    tax_ids = [line_vals['tax_line_id']]
                elif line_vals.get('tax_ids') and line_vals['tax_ids'][0][2]:
                    # Base line.
                    tax_ids = line_vals['tax_ids'][0][2]
                else:
                    continue

                for tax in self.env['account.tax'].browse(tax_ids).flatten_taxes_hierarchy():
                    for inv_rep_line, ref_rep_line in zip(tax.invoice_repartition_line_ids, tax.refund_repartition_line_ids):
                        mapping[inv_rep_line] = ref_rep_line
            return mapping

        move_vals = self.with_context(include_business_fields=True).copy_data(default=default_values)[0]

        tax_repartition_lines_mapping = compute_tax_repartition_lines_mapping(move_vals)

        for line_command in move_vals.get('line_ids', []):
            line_vals = line_command[2]  # (0, 0, {...})

            # ==== Inverse debit / credit / amount_currency ====
            amount_currency = -line_vals.get('amount_currency', 0.0)
            balance = line_vals['credit'] - line_vals['debit']

            line_vals.update({
                'amount_currency': amount_currency,
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })

            if move_vals['type'] not in ('out_refund', 'in_refund'):
                continue

            # ==== Map tax repartition lines ====
            if line_vals.get('tax_repartition_line_id'):
                # Tax line.
                invoice_repartition_line = self.env['account.tax.repartition.line'].browse(line_vals['tax_repartition_line_id'])
                if invoice_repartition_line not in tax_repartition_lines_mapping:
                    raise UserError(_("It seems that the taxes have been modified since the creation of the journal entry. You should create the credit note manually instead."))
                refund_repartition_line = tax_repartition_lines_mapping[invoice_repartition_line]

                # Find the right account.
                account_id = self.env['account.move.line']._get_default_tax_account(refund_repartition_line).id
                if not account_id:
                    if not invoice_repartition_line.account_id:
                        # Keep the current account as the current one comes from the base line.
                        account_id = line_vals['account_id']
                    else:
                        tax = invoice_repartition_line.invoice_tax_id
                        base_line = self.line_ids.filtered(lambda line: tax in line.tax_ids.flatten_taxes_hierarchy())[0]
                        account_id = base_line.account_id.id

                line_vals.update({
                    'tax_repartition_line_id': refund_repartition_line.id,
                    'account_id': account_id,
                    'tag_ids': [(6, 0, refund_repartition_line.tag_ids.ids)],
                })
            elif line_vals.get('tax_ids') and line_vals['tax_ids'][0][2]:
                # Base line.
                taxes = self.env['account.tax'].browse(line_vals['tax_ids'][0][2]).flatten_taxes_hierarchy()
                invoice_repartition_lines = taxes\
                    .mapped('invoice_repartition_line_ids')\
                    .filtered(lambda line: line.repartition_type == 'base')
                refund_repartition_lines = invoice_repartition_lines\
                    .mapped(lambda line: tax_repartition_lines_mapping[line])

                line_vals['tag_ids'] = [(6, 0, refund_repartition_lines.mapped('tag_ids').ids)]
        return move_vals

class SaleOrderSecondInherit(models.Model):
    _inherit = "sale.order"

    associated_stock_id = fields.Many2many(comodel_name='stock.picking',
                                    relation='stock_picking_sale_rel',
                                    column1='stock_picking_id',
                                    column2='sale_order_id')

    @api.onchange('associated_stock_id')
    def update_values(self):
        if self.order_line and self.refund_core == 'si':
            count = 0
            for line in self.order_line:
                count +=1
            updated_move_line_ids = [line.id for line in self.order_line]
            while count > 0:
                self.order_line = [(2, updated_move_line_ids[len(updated_move_line_ids) - count])]
                count = count - 1

        if isinstance(self.id, models.NewId):
            if self.associated_stock_id:
                move = []
                count = 0
                for line in self.associated_stock_id:
                    for order in line.move_ids_without_package:
                        new_line = self.write({'order_line':
                                                   [(0, 0, {'product_id': order.product_id.id,
                                                            'name': order.product_id.name,
                                                            'product_uom': order.product_id.uom_id.id,
                                                            'product_uom_qty': order.product_uom_qty})]})
                        self.order_line[len(self.order_line)-1].product_id_change()
                    # for a in line.valoracion_ids:
                    #     self.order_line[count]['price_unit'] = a.amount
                    #     count += 1

    def action_confirm(self):
        res = super(SaleOrderSecondInherit, self).action_confirm()
        if self.refund_core == 'si':
            self.automatic_book_entry()
            for line in self.associated_stock_id:
                line.es_devuelto = 'si'
        return res

    def automatic_book_entry(self):
        company_id = self.env['res.company'].search([('id', '=', 1)])
        account_debit_id = self.env['core.settings'].search([('name', '=', 'cxc_mtu')]).account.id
        account_credit_id = self.env['core.settings'].search([('name', '=', 'cxp_ops')]).account.id
        journal_id = request.env['account.journal'].search(
            [('devolucion_core', '=', 'si'), ('company_id', '=', company_id.id)])
        if not journal_id:
            raise Warning(_('Valla a los Diarios de la NV y seleccione el diario de devolución correspondiente'))
        monto = 0
        for line in self.order_line:
            monto = monto + line.price_subtotal
        if self.pricelist_id.currency_id.id == self.env.company.currency_id.id:
            currency_rate = self.env['res.currency.rate'].search([
                ('currency_id', '=', self.env.company.currency_id.id),
                ('name', '=', date.today()),
            ]).rate
            if not currency_rate:
                raise Warning(_('Ingrese una tasa para la fecha de hoy en el sistema'))
            monto = monto / currency_rate
        vals = {
            # 'name': name,
            'date': self.date_order,
            'journal_id': journal_id.id,
            'line_ids': False,
            'state': 'draft',
        }
        move_obj = request.env['account.move'].with_context(force_company=company_id.id)
        move_id = move_obj.create(vals)

        self.move_advance_ = {
            'account_id': account_credit_id,
            'company_id': self.company_id.id,
            'date_maturity': False,
            'date': self.date_order,
            'partner_id': self.partner_id.id,
            'move_id': move_id.id,
            'name': self.name,
            'journal_id': journal_id.id,
            'credit': monto,
            'debit': 0.0,
        }
        asiento = self.move_advance_
        move_line_obj = request.env['account.move.line']
        move_line_id1 = move_line_obj.with_context(check_move_validity=False).create(asiento)

        asiento['account_id'] = account_debit_id
        asiento['credit'] = 0.0
        asiento['debit'] = monto

        move_line_id2 = move_line_obj.create(asiento)
        move_id.action_post()

class JournalInherit(models.Model):
    _inherit = 'account.journal'

    devolucion_core = fields.Selection([('si', 'Si'), ('no', 'No')], string='Diario devolución Core', default='no')

