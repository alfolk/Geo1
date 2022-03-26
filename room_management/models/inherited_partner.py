from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


class ResPartnerInherited(models.Model):
    _inherit = 'res.partner'
    code = fields.Char('Code', store=True,tracking=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)',
         'Code of partner must be unique'),

    ]

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", "=", name), ("name", operator, name)]

        partners = self.search(domain + args, limit=limit)
        return partners.name_get()
