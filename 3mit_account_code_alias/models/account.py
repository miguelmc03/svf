# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from odoo.osv import expression

#----------------------------------------------------------
# Accounts
#----------------------------------------------------------


class AccountAccount(models.Model):
    _inherit = "account.account"

    code_alias = fields.Char(size=64, index=True)
    code = fields.Char(size=64, required=True, index=True, translate=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('code', '=ilike', name + '%'), ('code_alias', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()


    @api.depends('name', 'code', 'code_alias')
    def name_get(self):
        result = []
        for account in self:
            name = (account.code_alias or account.code) + ' ' + account.name + ' [' + account.company_id.name + ']'
            #name = account.code + ' ' + account.name
            result.append((account.id, name))
        return result

    #@api.onchange('code')
    #def onchange_code(self):
    #    self.code_alias = self.code

class AccountAccountTag(models.Model):
    _inherit = "account.account.tag"

    name = fields.Char(required=True, translate=True)





