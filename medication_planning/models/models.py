from odoo import models, fields, api, _
from odoo.exceptions import UserError

_STATES = [
    ('draft', 'Draft'),
    ('picking', 'Send Picking'),
    ('receive_med', 'Receive Medication'),
    ('close', 'Closed')
]


class product_edit(models.Model):
    _inherit = 'product.template'
    _description = 'Alfolk Medication Chart Record'

    pro_type = fields.Selection([('rivet', 'Rivet'), ('liquid ', 'Liquid'), ('injection', 'Injection')],
                                string='Medicine Type', store=True)
    medication = fields.Boolean('Medication', default=False)


class pickedit(models.Model):
    _inherit = 'stock.picking'

    med_id = fields.Many2one('medication.planning')

    def button_validate(self):
        for order in self:
            orders = self.env['medication.planning'].search([(
                'id', '=', order.med_id.id)])
            if orders:
                for line in order.move_line_ids:
                    for o in orders:
                        order_ = self.env['medication.planning.line'].search([(
                            'line_id', '=', o.id), ('medication', '=', line.product_id.id)])
                        if order_ and o.warehouse.out_type_id.id == order.picking_type_id.id:
                            orders.write({'state': 'receive_med',
                                          })
                            order_.write({'quantity_received': line.qty_done,
                                          })
                        elif order_ and o.warehouse.in_type_id.id == order.picking_type_id.id:
                            orders.write({'state': 'receive_med',
                                          })
                            order_.write({
                                'quantity_returned': line.qty_done,
                            })

            return super(pickedit, self).button_validate()


class alfolk_medication_chart_record(models.Model):
    _name = 'medication.planning'
    _description = 'Medication Planned'
    _rec_name = 'person'

    def unlink(self):
        for l in self:
            if  l.state != 'draft':
                raise UserError(_('Cannot delete a item in post state'))
            return super(alfolk_medication_chart_record, self).unlink()


    @api.depends('line_id.quantity_re')
    def get_total_return(self):
        for sale in self:
            if sale.line_id:
                sale.total = sum(sale.line_id.mapped('quantity_re'))
            else:
                sale.total = sale.line_id.quantity_re

    total = fields.Float(compute='get_total_return', store=True)

    warehouse = fields.Many2one('stock.warehouse', store=True, required=True, string="Warehouse")
    location = fields.Many2one(
        'stock.location', store=True,
    )
    location_des = fields.Many2one(
        'stock.location', store=True, related='person.property_stock_customer',
        check_company=True, readonly=True, required=True,
    )
    picking_type = fields.Many2one(
        'stock.picking.type', store=True
    )
    picking_ids = fields.One2many('stock.picking', 'med_id', string='Transfers')
    delivery_count = fields.Integer(string='Delivery Orders', compute='_compute_picking_ids')

    @api.depends('picking_ids')
    def _compute_picking_ids(self):
        for order in self:
            order.delivery_count = len(order.picking_ids)

    def action_view_delivery(self):
        return self._get_action_view_picking(self.picking_ids)

    def _get_action_view_picking(self, pickings):
        '''
        This function returns an action that display existing delivery orders
        of given sales order ids. It can either be a in a list or in a form
        view, if there is only one delivery order to show.
        '''
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_all")

        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif pickings:
            form_view = [(self.env.ref('stock.view_picking_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = pickings.id
        # Prepare the context.
        picking_id = pickings.filtered(lambda l: l.picking_type_id.code == 'outgoing')
        if picking_id:
            picking_id = picking_id[0]
        else:
            picking_id = pickings[0]
        action['context'] = dict(self._context, default_partner_id=self.person.id,
                                 default_picking_type_id=picking_id.picking_type_id.id, default_origin=self.id,
                                 default_group_id=picking_id.group_id.id)
        return action

    def close(self):
        self.write({'state': 'close'})

    def create_picking(self):
        for record in self:
            picking = self.env['stock.picking'].create({
                'partner_id': record.person.id,
                'location_id': record.warehouse.lot_stock_id.id,
                'location_dest_id': record.person.property_stock_customer.id,
                'picking_type_id': record.warehouse.out_type_id.id,
                'med_id': record.id,
                'state': 'confirmed',

            })
            for line in record.line_id:
                self.env['stock.move'].create({
                    'picking_id': picking.id,
                    'product_id': line.medication.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_uom_id.id,
                    'location_id': record.warehouse.lot_stock_id.id,
                    'location_dest_id': record.person.property_stock_customer.id,
                    'name': '/',

                })
            picking.action_confirm()
            self.write({'state': 'picking',

                        })

    def create_residual(self):
        for record in self:
            for x in record.line_id:
                if x.quantity_re > 0:
                    picking = self.env['stock.picking'].create({
                        'partner_id': record.person.id,
                        'location_id': record.person.property_stock_customer.id,
                        'location_dest_id': record.warehouse.lot_stock_id.id,
                        'picking_type_id': record.warehouse.in_type_id.id,
                        'med_id': record.id,
                        'state': 'confirmed',

                    })
                    for line in record.line_id:
                        if line.quantity_re > 0:
                            x = line.quantity_returned + line.product_uom_ids._compute_quantity(line.quantity_re,
                                                                                                line.product_uom_id,
                                                                                                rounding_method='HALF-UP')
                            if x <= line.quantity_received:
                                self.env['stock.move'].create({
                                    'picking_id': picking.id,
                                    'product_id': line.medication.id,
                                    'product_uom_qty': line.quantity_re,
                                    'product_uom': line.product_uom_ids.id,
                                    'location_id': record.person.property_stock_customer.id,
                                    'location_dest_id': record.warehouse.lot_stock_id.id,
                                    'name': '/',

                                })

                            else:
                                raise UserError(
                                    _("Cannot Return Quantity More than quantity Received"))

                            line.quantity_returned += line.product_uom_ids._compute_quantity(line.quantity_re,
                                                                                             line.product_uom_id,
                                                                                             rounding_method='HALF-UP')
                            line.quantity_re = 0
                            line.product_uom_ids = False

                    picking.action_confirm()

    @api.model
    def _get_default_employee_id(self):
        return self.env['res.users'].browse(self.env.uid)

    employee_id = fields.Many2one('res.users',
                                  'Employee',
                                  visibility='onchange', readonly=True, invisible=True,
                                  default=_get_default_employee_id, copy=False, store=True)

    @api.depends('employee_id')
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.employee_id.company_id

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 store=True, readonly=True, invisible=True,
                                 compute='_compute_company_id')

    person = fields.Many2one('res.partner', string='Person', store=True, required=True)
    medication_duration = fields.Char('Medicine Duration', store=True)
    line_id = fields.One2many('medication.planning.line', 'line_id')
    line_ids = fields.One2many('medication.planning.day', 'line_ids')
    state = fields.Selection(selection=_STATES, string='Status', index=True, track_visibility='onchange', required=True,
                             copy=False, default='draft', store=True)

    @api.model
    def _getproduct(self):
        for record in self:
            t = []
            for r in record.line_id:
                product = self.env['medication.planning.line'].search(
                    [('line_id', '=', record.id)])
                for line in product:
                    t.append(line.medication.id)

            return t

    @api.depends('person')
    def _load_all_partner_ids(self):
        for record in self:
            if record.person:
                record.products = record._getproduct()
            else:
                record.products = False

    products = fields.Many2many('product.product', store=False, compute='_load_all_partner_ids')

    def action_register_day(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        return {
            'name': _('Register Day'),
            'res_model': 'medication.planning.day',
            'view_mode': 'form',
            'context': {
                'active_model': 'medication.planning',
                'active_ids': self.ids,
                'default_line_ids': self.id
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class alfolk_medication_chart_record_line(models.Model):
    _name = 'medication.planning.line'
    _description = 'Medication Planning Line'

    line_id = fields.Many2one('medication.planning', ondelete="cascade", store=True)
    medication = fields.Many2one('product.product',
                                 domain="[('medication','=',True)]",
                                 string='Medicine', store=True)
    quantity = fields.Float('Qty Ordered', store=True)
    state = fields.Selection(related='line_id.state', store=True)
    quantity_received = fields.Float('Qty Received', store=True)
    quantity_returned = fields.Float('Qty Returned', store=True)
    quantity_re = fields.Float('Qty To Return', store=True)
    employee = fields.Many2one('hr.employee', string='Employee', store=True)
    notes = fields.Char(string='Notes', store=True)

    @api.onchange('medication')
    def onchange_field_account(self):
        if self.medication:
            domain = {'product_uom_id': [('category_id', '=', self.medication.uom_id.category_id.id)]}
            return {'domain': domain}
        else:
            return {'domain': False}

    @api.onchange('quantity_re')
    def onchange_field_uom_category(self):
        if self.quantity_re:
            domain = {'product_uom_ids': [('category_id', '=', self.medication.uom_id.category_id.id)]}
            return {'domain': domain}
        else:
            return {'domain': False}

    @api.onchange('medication')
    def _getline1(self):
        if self.medication:
            employees = self.env['product.product'].search([('id', '=', self.medication.id),
                                                       ])
        
            self.product_uom_id=(employees.uom_id.id)
            self.product_uom_ids=(employees.uom_id.id)


    product_uom_id = fields.Many2one('uom.uom',string= 'Unit of Measure', default=_getline1,store=True)

    product_uom_ids = fields.Many2one('uom.uom',string= 'Unit of Measure', store=True)


class alfolk_medication_chart_record_day(models.Model):
    _name = 'medication.planning.day'
    _description = 'Alfolk Medication Chart Record Day'
    line_ids = fields.Many2one('medication.planning', ondelete="cascade", string='Medication', store=True)
    state = fields.Selection(related='line_ids.state', store=True)

    medication = fields.Many2one('product.product', required=True, domain="[('id', 'in',products)]", string='Medicine',
                                 store=True)
    day = fields.Datetime(string='Day With Hour', required=True, store=True)
    quantity = fields.Char(string='Quantity', required=True, store=True)

    @api.onchange('medication')
    def onchange_field_uom_category(self):
        if self.medication:
            domain = {'product_uom_id': [('category_id', '=', self.medication.uom_id.category_id.id)]}
            return {'domain': domain}
        else:
            return {'domain': False}

    product_uom_id = fields.Many2one('uom.uom', 'Unit of Measure', required=True, store=True)

    @api.depends('quantity', 'line_ids', 'medication')
    def _compute_quantity(self):
        for line in self:
            if line.line_ids:
                product = self.env['medication.planning.line'].search(
                    [('line_id', '=', line.line_ids.id), ('medication', '=', line.medication.id)])
                if product:
                    line.quantity_received = product.quantity_received
                else:
                    line.quantity_received = 0
            if line.medication:
                product_re = self.env['medication.planning.day'].search(
                    [('line_ids', '=', line.line_ids.id), ('medication', '=', line.medication.id)])
                sum = 0
                if product_re:
                    for r in product_re:
                        sum += r.quantity
                        line.quantity_re = line.quantity_received - sum
                else:
                    line.quantity_re = 0

    quantity_received = fields.Float(string='Quantity received', compute='_compute_quantity', store=True)
    quantity_re = fields.Float(string='Quantity re', compute='_compute_quantity', store=True)
    employee = fields.Many2one('hr.employee', required=True, string='Employee', store=True)
    products = fields.Many2many('product.product', string='product', store=False, related='line_ids.products', )
    is_taken = fields.Boolean(string='IS Taken?', store=True)
