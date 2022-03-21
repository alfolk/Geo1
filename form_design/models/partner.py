from odoo import models, fields, api, _
from odoo.exceptions import UserError
from calendar import monthrange


class Partner(models.Model):
    _inherit = 'res.partner'

    def open_medical_form(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'medical'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'medical'), '|', ('category', '=', record.category.id), ('category', '=', False)])
                for form in forms:
                    lines = []
                    for line in form.question_ids:
                        lines.append((0, 0, {
                            'name': line.title,
                            'sequence': line.sequence,
                            'form_line_id': line._origin.id,
                            'user_id': line.user_id.id,
                            'form_id': form._origin.id,
                            'question_type': line.question_type,
                            'matrix_answer_type': line.matrix_answer_type,
                        }))
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain':  [('form_type', '=', 'medical'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_physical_measurements(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'physical'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'physical'), '|', ('category', '=', record.category.id), ('category', '=', False)])
                for form in forms:
                    lines = []
                    for line in form.question_ids:
                        lines.append((0, 0, {
                            'name': line.title,
                            'sequence': line.sequence,
                            'form_line_id': line._origin.id,
                            'user_id': line.user_id.id,
                            'form_id': form._origin.id,
                            'question_type': line.question_type,
                            'matrix_answer_type': line.matrix_answer_type,
                        }))
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain':  [('form_type', '=', 'physical'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_nutrition(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'nutrition'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'nutrition'), '|', ('category', '=', record.category.id), ('category', '=', False)])
                for form in forms:
                    lines = []
                    for line in form.question_ids:
                        lines.append((0, 0, {
                            'name': line.title,
                            'sequence': line.sequence,
                            'form_line_id': line._origin.id,
                            'user_id': line.user_id.id,
                            'form_id': form._origin.id,
                            'question_type': line.question_type,
                            'matrix_answer_type': line.matrix_answer_type,
                        }))
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'nutrition'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    def open_achievement_rate(self):
        for record in self:
            ids = []
            exist = record.env['form.apply'].search([('form_type', '=', 'achievement'), ('partner_id', '=', record.id),
                                                     ('date', '=', fields.date.today())])
            ids = exist.ids
            if not exist:
                forms = record.env['form.design'].search(
                    [('type', '=', 'achievement'), '|', ('category', '=', record.category.id),
                     ('category', '=', False)])
                for form in forms:
                    lines = []
                    for line in form.question_ids:
                        lines.append((0, 0, {
                            'name': line.title,
                            'sequence': line.sequence,
                            'form_line_id': line._origin.id,
                            'user_id': line.user_id.id,
                            'form_id': form._origin.id,
                            'question_type': line.question_type,
                            'matrix_answer_type': line.matrix_answer_type,
                        }))
                    record.env['form.apply'].create({
                        'form_id': form.id,
                        'partner_id': record.id,
                        'date': fields.date.today(),
                        'apply_ids': lines,

                    })

            return {
                'name': _(f'Filled out forms of {record.name}'),
                'type': 'ir.actions.act_window',
                'res_model': 'form.apply',
                'view_mode': 'tree,form',
                'domain': [('form_type', '=', 'achievement'), ('partner_id', '=', record.id), ('state', '=', 'draft')],
                'context': "{'default_partner_id': " + str(self._origin.id) + "}",
            }

    is_student = fields.Boolean(compute='_compute_is_student',store=False)

    @api.onchange('category')
    def _compute_is_student(self):
        for record in self:
            if record.category.category_type:
                record.is_student = True
            else:
                record.is_student = False
