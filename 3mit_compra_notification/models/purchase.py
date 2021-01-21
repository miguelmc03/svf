from odoo import api, fields, models, _
from odoo.exceptions import Warning
from odoo.http import request
from odoo.tests import Form, tagged
class CompanyEdit(models.Model):
    _inherit = "res.company"
    compra_notification = fields.Boolean(default=False)
    
class Purchasenotification(models.Model):
    _inherit = "purchase.order"

    email_to = fields.Char()
    name_usuario = fields.Char()

    def button_confirm(self):
        res = super(Purchasenotification, self).button_confirm()
        if self.company_id.compra_notification == True:
            self.enviar_correos_automatico()
        return res
    
    def enviar_correos_automatico(self):
        template = self.env.ref('3mit_compra_notification.template_compra_email', False)
        grupo_id = self.env['res.groups'].search([('name', '=', 'Notificación de compras'), ('category_id.name', '=', 'Compra')], order='id desc')
        for move in self:
            if grupo_id and grupo_id.users:
                for sent in grupo_id.users:
                    move.email_to = sent.login
                    move.name_usuario = sent.name
                    template.send_mail(move.id, force_send=True)
        return True


