# -*- coding: utf-8 -*-
# from odoo import http


# class CertificationSemences(http.Controller):
#     @http.route('/certification_semences/certification_semences', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/certification_semences/certification_semences/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('certification_semences.listing', {
#             'root': '/certification_semences/certification_semences',
#             'objects': http.request.env['certification_semences.certification_semences'].search([]),
#         })

#     @http.route('/certification_semences/certification_semences/objects/<model("certification_semences.certification_semences"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('certification_semences.object', {
#             'object': obj
#         })
