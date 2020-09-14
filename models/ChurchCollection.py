# -*- coding:utf-8 -*-
"""Church Collections consists of all church weekly or monthly collections."""
from odoo.addons.ng_church.models.helper import parish

from odoo import api, fields, models
from odoo.exceptions import AccessError,\
    MissingError, UserError, ValidationError


class Collection(models.Model):
    """Ng Church Collection Model."""

    _name = 'ng_church.collection'
    _description = "NG Church Collection"

    name = fields.Char(string="Name")


class Donation(models.Model):
    """Donation Model.

    Church Donation is cetain sum of money that is given
    to a church as charity.
    """

    _name = 'ng_church.donation'
    _description = "NG Church Donation"

    name = fields.Many2one('project.project', 'Project', required=True)
    start_date = fields.Date(related='name.x_date', string='Start Date')
    notes = fields.Text(string='Note')
    church_id = fields.Many2one('res.company', default=parish)
    donation_line_ids = fields.One2many('ng_church.donation_line',
                                        'donation_id', srting='Donations')


class DonationLine(models.Model):
    """Donation Line Model.

    Church Donation is cetain sum of money that is
    given to a church as charity.
    """

    _name = 'ng_church.donation_line'
    _description = "NG Church Donation Line"

    donation_id = fields.Many2one('ng_church.donation', string='Donation')
    name = fields.Char(string='Name')
    date = fields.Date(string='Date', required=True)
    donor_id = fields.Many2one('res.partner', string='Donor')
    amount = fields.Float(string='Donated Amount', required=True)
    is_invoiced = fields.Boolean(string='Invoiced', readonly=True)
    notes = fields.Char(related='donation_id.name.name', string="Notes")
    church_id = fields.Many2one('res.company', default=parish)

    @api.constrains('amount')
    def _check_valid_amount(self):
        for donation_l in self:
            if donation_l.amount < 1:
                raise ValidationError('Please enter a valid amount of'
                                      ' money {} can\'t be'
                                      ' deposited'.format(self.amount))

    @api.onchange('date')
    def _onchange_name(self):
        if self.date:
            self.name = self.date.strftime("%B %d, %Y")

    def _prepare_account_voucher(self):
        """Generate Account Voucher."""
        company = self.env.user and self.env.user.company_id or False
        voucher = voucher.create({
            'company_id': company and company.id or False,
            'partner_id': self.env.user.partner_id.id,
            'pay_now': 'pay_now',
            'account_id': company and company.transit_account and
            company.transit_account.id or False,
            'journal_id': company and company.donation_journal and
            company.donation_journal.id or False,
            'name': '{} Donation'.format(self.donor_id.name or 'Anonymous'),
            'voucher_type': 'sale'
        })
        return voucher

    def _prepare_account_voucher_line(self, voucher_id):
        payload = {
            'name': self.notes,
            # Quantity is intentionally hard coded to be int: 1.
            'quantity': 1,
            'price_unit': self.amount,
            'voucher_id': voucher_id and voucher_id.id or False,
            # credit account
            'account_id': self.env.user.company_id and \
            self.env.user.company_id.donation_account and \
            self.env.user.company_id.donation_account.id or False
        }
        return voucher_line.create(payload)

    def generate_donation_voucher(self):
        """User Interface button call this method."""
        voucher_id = self._prepare_account_voucher()
        self._prepare_account_voucher_line(voucher_id)
        self.is_invoiced = True


class Tithe(models.Model):
    """Tithe Model.

    One tenth of produce or earnings, formerly taken as a tax for
    the support of the church and clergy.
    """

    _name = 'ng_church.tithe'
    _description = "NG Church Tithe"

    @api.model
    def default_get(self, fields):
        """Default Get method."""
        res = super(Tithe, self).default_get(fields)
        category = self.env['ng_church.collection'].search([
            ('name', '=', 'Tithes')], limit=1)
        if not category:
            category = self.env['ng_church.collection'].create(
                {'name': 'Tithes'})
        res.update({
            'name': category.id,
        })
        return res

    name = fields.Many2one('ng_church.collection', string='Collection')
    section_id = fields.Many2one(
        'church.sections', string="Church Section", required=True)
    service_id = fields.Many2one('ng_church.program', string="Church Service")
    pastor_id = fields.Many2one('ng_church.pastor', string='Minister\'s Name')
    church_id = fields.Many2one(
        'res.company', string='Church\'s Tithe', default=parish)
    is_pastor_tithe = fields.Boolean(string='Minister\'s Tithe')
    tithe_line_ids = fields.One2many('ng_church.tithe_lines', 'tithe_id',
                                     string='Tithes')


class TitheLine(models.Model):
    """TitheLine Model.

    One tenth of produce or earnings,
    formerly taken as a tax for the support of the church and clergy.
    """

    _name = 'ng_church.tithe_lines'
    _description = "NG Church Tithe Lines"

    date = fields.Date(string='Date', required=True)
    name = fields.Char(string='Name')
    tithe_type = fields.Selection(
        selection=[('members', 'Members'), ('pastor', 'Pastor'),
                   ('minister', 'Minister')], string='Category',
        default='members')
    tither = fields.Many2one('res.partner', string='Tither Name')
    is_invoiced = fields.Boolean(string='Invoiced', readonly=True)
    tithe_id = fields.Many2one('ng_church.tithe', string='Tithe')
    amount = fields.Float('Amount', required=True)
    church_id = fields.Many2one('res.company', default=parish)

    @api.constrains('amount')
    def _check_valid_amount(self):
        for tithe_l in self:
            if tithe_l.amount < 1:
                raise ValidationError('Please enter a valid amount of'
                                      ' money {} can\'t be'
                                      ' deposited'.format(tithe_l.amount))

    @api.onchange('date')
    def _onchange_name(self):
        if self.date:
            self.name = self.date.strftime("%B %d, %Y")

    def _prepare_account_voucher(self):
        """Generate Account Voucher."""
        company = self.env.user.company_id
        payload = {
            'company_id': company.id,
            'partner_id': self.env.user.partner_id.id,
            'pay_now': 'pay_now',
            'account_id': company.transit_account.id,
            'journal_id': company.tithe_journal.id,
            'name': '{} Tithe'.format(self.tithe_type.capitalize()),
            'voucher_type': 'sale'

        }
        voucher = voucher.create(payload)
        return voucher

    def _prepare_account_voucher_line(self, voucher_id):
        payload = {
            'name': 'Tithe',
            # Quantity is intentionally hard coded to be int: 1.
            'quantity': 1,
            'price_unit': self.amount,
            'voucher_id': voucher_id.id,
            # credit account
            'account_id': self.env.user.company_id.tithe_account.id
        }
        return voucher_line.create(payload)

    def generate_tithe_voucher(self):
        """User Interface button call this method."""
        voucher_id = self._prepare_account_voucher()
        self._prepare_account_voucher_line(voucher_id)
        self.is_invoiced = True


class Offering(models.Model):
    """Church Offering Model."""

    _name = 'ng_church.offering'
    _description = "NG Church Offering"

    @api.model
    def default_get(self, fields):
        """Default Get method."""
        res = super(Offering, self).default_get(fields)
        category = self.env['ng_church.collection'].search([
            ('name', '=', 'Offering')], limit=1)
        if not category:
            category = self.env['ng_church.collection'].create(
                {'name': 'Offering'})
        res.update({
            'name': category.id,
        })
        return res

    name = fields.Many2one('ng_church.collection', string='Collection Source')
    section_id = fields.Many2one('church.sections', string="Church Section",
                                 required=True)
    service_id = fields.Many2one('ng_church.program', string="Church Service")
    church_id = fields.Many2one('res.company', default=parish)
    offering_line_ids = fields.One2many('ng_church.offering_line',
                                        'offering_id', string='Offering')


class OfferingLine(models.Model):
    """Church Offering lines model."""

    _name = 'ng_church.offering_line'
    _description = "NG Church Offering Line"

    date = fields.Date(string='Date', required=True)
    name = fields.Char(string='Name')
    is_invoiced = fields.Boolean(string='Invoiced')
    amount = fields.Float(string='Amount')
    offering_id = fields.Many2one('ng_church.offering', string='Offering')
    church_id = fields.Many2one('res.company', default=parish)

    @api.constrains('amount')
    def _check_valid_amount(self):
        for offering_l in self:
            if offering_l.amount < 1:
                raise ValidationError('Please enter a valid amount of'
                                      ' money {} can\'t be'
                                      ' deposited'.format(offering_l.amount))

    @api.onchange('date')
    def _onchange_name(self):
        if self.date:
            self.name = self.date.strftime("%B %d, %Y")

    def _prepare_account_voucher(self):
        """Generate Account Voucher."""
        company = self.env.user.company_id
        payload = {
            'company_id': company.id,
            'partner_id': self.env.user.partner_id.id,
            'pay_now': 'pay_now',
            'account_id': company.transit_account.id,
            'journal_id': company.offering_journal.id,
            'name': '{} Offering'.format(self.offering_id.section_id.name),
            'voucher_type': 'sale'
        }
        voucher = voucher.create(payload)
        return voucher

    def _prepare_account_voucher_line(self, voucher_id):
        payload = {
            'name': 'Offering',
            # Quantity is intentionally hard coded to be int: 1.
            'quantity': 1,
            'price_unit': self.amount,
            'voucher_id': voucher_id and voucher_id.id or False,
            # credit account
            'account_id': self.env.user and \
            self.env.user.company_id and \
            self.env.user.company_id.offering_account and \
            self.env.user.company_id.offering_account.id or False
        }
        return voucher_line.create(payload)

    def generate_offering_voucher(self):
        """User Interface button call this method."""
        if self._uid != self.write_uid.id:
            raise AccessError(
                'You don\'t have the permission to Draft this invoice')
            return False
        voucher_id = self._prepare_account_voucher()
        voucher_line_id = self._prepare_account_voucher_line(voucher_id)
        self.is_invoiced = True
        return voucher_line_id


class Pledge(models.Model):
    """."""

    _name = 'ng_church.pledge'
    _description = "NG Church Pledge"

    name = fields.Many2one('project.project', string='Project', required=True)
    date = fields.Date(related='name.x_date', string='Date')
    church_id = fields.Many2one('res.company', default=parish)
    pledge_line_ids = fields.One2many('ng_church.pledge_line', 'pledge_id',
                                      string='Pledges')


class PledgeLine(models.Model):
    """."""

    _name = 'ng_church.pledge_line'
    _description = "NG Church Pledge Line"

    name = fields.Char(string='Name', related='pledge_id.name.name')
    date = fields.Date(string='Pledged Date', required=True)
    pledger = fields.Many2one('ng_church.associate', string='Pledger')
    amount = fields.Float(string='Pledged Amount')
    balance = fields.Float(string='Balance',
                           compute='_compute_balance', store=True)
    paid = fields.Float(string='Paid', compute='_compute_total_paid',
                        store=True)
    is_invoiced = fields.Char(string='Invoiced', default=False)
    state = fields.Selection(selection=[('active', 'Active'),
                                        ('fulfilled', 'Fulfilled')],
                             default='active')
    pledge_id = fields.Many2one('ng_church.pledge', string='Pledge')
    pledge_line_payment_ids = fields.One2many('ng_church.pledge_line_payment',
                                              'pledge_line_id',
                                              string='Pledge Payment')

    @api.constrains('amount')
    def _check_valid_amount(self):
        for pledge_l in self:
            if pledge_l.amount < 1:
                raise ValidationError('Please enter a valid amount of'
                                      ' money {} can\'t be'
                                      ' pledged'.format(pledge_l.amount))

    @api.depends('pledge_line_payment_ids')
    def _compute_total_paid(self):
        for pledge_l in self:
            total = 0
            for pledge_line_id in self.pledge_line_payment_ids:
                for pledge in pledge_line_id:
                    total += pledge.amount
            pledge_l.paid = total

    @api.depends('paid')
    def _compute_balance(self):
        for pledge_l in self:
            if pledge_l.paid >= pledge_l.amount:
                pledge_l.write({'state': 'fulfilled'})
            else:
                pledge_l.write({'state': 'active'})
            pledge_l.balance = 0.0 if (pledge_l.amount - pledge_l.paid) < 1 \
                else (pledge_l.amount - pledge_l.paid)

    def send_by_email(self):
        """Send report via email."""
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'ng_church', 'ng_church_pledge_payment_email_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'ng_church.pledge_line',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        }
        return {
            'name': 'Compose Email',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def message_get_reply_to(self, res_id, default=None):
        """message_get_reply_to."""
        if self.env.user.company_id.email is False:
            raise MissingError('Set church email address')
        return {res_id[0]: self.env.user.company_id.email}

    def print_report(self):
        """Direct Report printing."""
        return self.env['report'].get_action(self,
                                             'ng_church.print_pledge_report')

    def _prepare_account_voucher(self):
        """Generate Account Invoice."""
        company = self.env.user.company_id
        voucher = voucher.create({
            'partner_id': company.partner_id.id,
            'pay_now': 'pay_now',
            'account_id': company.transit_account.id,
            'journal_id': company.pledge_journal.id,
            'name': '{} Pledge'.format(self.name),
            'voucher_type': 'sale'

        })
        return voucher

    def _prepare_account_voucher_line(self, voucher_id):
        company = self.env.user.company_id
        payload = {
            'name': voucher_id.name,
            # Quantity is intentionally hard coded to be int: 1.
            'quantity': 1,
            'price_unit': self.paid,
            'voucher_id': voucher_id.id,
            'account_id': company.pledge_account.id
        }
        return voucher_line.create(payload)

    def generate_pledge_voucher(self):
        """User Interface button call this method."""
        if not self.is_invoiced:
            voucher_id = self._prepare_account_voucher()
            voucher_line_id = self._prepare_account_voucher_line(voucher_id)
            self.is_invoiced = True
            return voucher_line_id
        raise UserError('Voucher already existed')


class PledgeLinePayment(models.Model):
    """Ng Church Pledge Line Payment."""

    _name = 'ng_church.pledge_line_payment'
    _description = "NG Church Pledge Line Payment"

    date = fields.Date(string='Date', required=True)
    amount = fields.Float(string='Amount')
    pledge_line_id = fields.Many2one('ng_church.pledge_line')

    @api.constrains('amount')
    def _check_valid_amount(self):
        for pledge_l in self:
            if pledge_l.amount < 1:
                raise ValidationError('Please enter a valid amount of'
                                      ' money {} can\'t be'
                                      ' deposited'.format(pledge_l.amount))
