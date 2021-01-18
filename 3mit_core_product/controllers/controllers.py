# -*- coding: utf-8 -*-
# from odoo import http


# class 3mitCoreProduct(http.Controller):
#     @http.route('/3mit_core_product/3mit_core_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/3mit_core_product/3mit_core_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('3mit_core_product.listing', {
#             'root': '/3mit_core_product/3mit_core_product',
#             'objects': http.request.env['3mit_core_product.3mit_core_product'].search([]),
#         })

#     @http.route('/3mit_core_product/3mit_core_product/objects/<model("3mit_core_product.3mit_core_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('3mit_core_product.object', {
#             'object': obj
#         })
