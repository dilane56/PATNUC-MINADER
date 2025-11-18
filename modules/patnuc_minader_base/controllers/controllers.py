# -*- coding: utf-8 -*-
# from odoo import http


# class PatnucMinaderBase(http.Controller):
#     @http.route('/patnuc_minader_base/patnuc_minader_base', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/patnuc_minader_base/patnuc_minader_base/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('patnuc_minader_base.listing', {
#             'root': '/patnuc_minader_base/patnuc_minader_base',
#             'objects': http.request.env['patnuc_minader_base.patnuc_minader_base'].search([]),
#         })

#     @http.route('/patnuc_minader_base/patnuc_minader_base/objects/<model("patnuc_minader_base.patnuc_minader_base"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('patnuc_minader_base.object', {
#             'object': obj
#         })

