# -*- coding: utf-8 -*-
# from odoo import http


# class 3mitChangesCrm(http.Controller):
#     @http.route('/3mit_changes_crm/3mit_changes_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/3mit_changes_crm/3mit_changes_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('3mit_changes_crm.listing', {
#             'root': '/3mit_changes_crm/3mit_changes_crm',
#             'objects': http.request.env['3mit_changes_crm.3mit_changes_crm'].search([]),
#         })

#     @http.route('/3mit_changes_crm/3mit_changes_crm/objects/<model("3mit_changes_crm.3mit_changes_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('3mit_changes_crm.object', {
#             'object': obj
#         })
