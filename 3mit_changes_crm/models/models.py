# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError
from odoo.exceptions import Warning

class Lead2OpportunityPartner(models.TransientModel):

    _inherit = 'crm.lead2opportunity.partner'

    actionb = fields.Selection([
        ('exist', 'Enlazar a cliente existente'),
        ('nothing', 'No enlazar a un cliente')
    ], 'Related Customer', required=True)

    @api.onchange("actionb")
    def cambio_actionb(self):
        self.action = self.actionb
# class 3mit_changes_crm(models.Model):
#     _name = '3mit_changes_crm.3mit_changes_crm'
#     _description = '3mit_changes_crm.3mit_changes_crm'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
class Lead(models.Model):
    _inherit = "crm.lead"

    record_customer = fields.Boolean(default=False)
    record_cliente = fields.Boolean(default=False)

    def action_set_won_rainbowman(self):
        self.record_customer = True
        self.record_cliente = True
        res = super(Lead, self).action_set_won_rainbowman()
        return res

    @api.onchange('stage_id')
    def cambio_stage(self):
        if self.stage_id.is_won:
            self.record_customer = True
        if self.stage_id.crear_cliente == 'si':
            self.record_cliente = True

    def action_simple_sale_quotations_new(self):
        if not self.partner_id:
            raise Warning(_('Debe crear y seleccionar el cliente al cual se le realizara el presupuesto'))
        else:
            return self.action_simple_new_quotation()

    def action_simple_new_quotation(self):
        action = self.env.ref("3mit_changes_crm.sale_action_quotations_new").read()[0]
        action['context'] = {
            'search_default_opportunity_id': self.id,
            'default_opportunity_id': self.id,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_team_id': self.team_id.id,
            'default_campaign_id': self.campaign_id.id,
            'default_medium_id': self.medium_id.id,
            'default_origin': self.name,
            'default_source_id': self.source_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
        }
        return action

    def action_simple_new_quotation_2(self):
        action = self.env.ref("3mit_changes_crm.sale_action_quotations_new").read()[0]
        return action

class Stage(models.Model):
    _inherit = 'crm.stage'

    crear_cliente = fields.Selection([('si', 'Si'),('no', 'No')])
