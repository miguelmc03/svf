from datetime import datetime, date, timedelta
import locale
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo.exceptions import UserError
from datetime import timedelta, date, datetime
from io import BytesIO
import xlwt, base64
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class ReportSale(models.TransientModel):
    _name = 'wizard.customer.request'
    _description = 'Open customer request'

    user = fields.Many2one('res.users', required=True)
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    send = fields.Boolean('Send?', readonly=True)

    def action_create_cliente(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        crm_lead_obj = self.env['crm.lead']
        slip = crm_lead_obj.browse(self._context['active_id'])
        template = self.env.ref('3mit_changes_crm.email_template_slip_1', False)
        correo = self.user.email
        email_values = {'email_to': correo}
        template.send_mail(slip.id, force_send=True, email_values=email_values)
        return True
