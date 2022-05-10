# -*- coding: utf-8 -*-
# from odoo import http


# class InvoiceSequence(http.Controller):
#     @http.route('/invoice_sequence/invoice_sequence', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_sequence/invoice_sequence/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_sequence.listing', {
#             'root': '/invoice_sequence/invoice_sequence',
#             'objects': http.request.env['invoice_sequence.invoice_sequence'].search([]),
#         })

#     @http.route('/invoice_sequence/invoice_sequence/objects/<model("invoice_sequence.invoice_sequence"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_sequence.object', {
#             'object': obj
#         })
