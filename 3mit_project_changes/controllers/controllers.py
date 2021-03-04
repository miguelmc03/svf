# -*- coding: utf-8 -*-
# from odoo import http


# class 3mitProjectChanges(http.Controller):
#     @http.route('/3mit_project_changes/3mit_project_changes/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/3mit_project_changes/3mit_project_changes/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('3mit_project_changes.listing', {
#             'root': '/3mit_project_changes/3mit_project_changes',
#             'objects': http.request.env['3mit_project_changes.3mit_project_changes'].search([]),
#         })

#     @http.route('/3mit_project_changes/3mit_project_changes/objects/<model("3mit_project_changes.3mit_project_changes"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('3mit_project_changes.object', {
#             'object': obj
#         })
