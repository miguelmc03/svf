# -*- coding: utf-8 -*-
# from odoo import http


# class 3mitDevolutionCore(http.Controller):
#     @http.route('/3mit_refund_core/3mit_refund_core/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/3mit_refund_core/3mit_refund_core/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('3mit_refund_core.listing', {
#             'root': '/3mit_refund_core/3mit_refund_core',
#             'objects': http.request.env['3mit_refund_core.3mit_refund_core'].search([]),
#         })

#     @http.route('/3mit_refund_core/3mit_refund_core/objects/<model("3mit_refund_core.3mit_refund_core"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('3mit_refund_core.object', {
#             'object': obj
#         })
