# -*- coding:utf-8 -*-
"""."""
from odoo import api, fields, models
from .helper import parish, parish_partner
from odoo.exceptions import UserError, ValidationError, MissingError


class Lodgement(models.Model):
    """."""

    _name = 'ng_church.lodgement'
    _description = "NG Church Lodgement"

    def _get_default_journal(self):
        if self.env.user.company_id.transit_journal.id:
            return self.env.user.company_id.transit_journal.id
        raise UserError('Church Transist account is not set.')
    name = fields.Char(string='Name', default='Church Lodgement')
    date = fields.Date(string='Date', required=True)
    amount = fields.Float(string='Amount', required=True)
    description = fields.Text(string='Note', required=True)
    church_id = fields.Many2one('res.company', default=parish)
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain=[('type', '=', 'bank')], required=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')],
                             copy=False, default='draft')

    @api.constrains('amount')
    def _check_valid_amount(self):
        for ledgement in self:
            if ledgement.amount < 1:
                raise ValidationError('Please enter a valid amount of'
                                      ' money {} amount can\'t be post for'
                                      ' lodgement'.format(ledgement.amount))

    def _prepare_account_move(self):
        account_move = self.env['account.move']
        account_move = account_move.create({
            'journal_id': self.journal_id.id,
            # 'amount': self.amount,
            'partner_id': parish_partner(self),
            'date': self.date
        })
        return account_move

    def _prepare_first_account_move_line(self, move_id):
        if self.env.user and self.env.user.company_id and \
                not self.env.user.company_id.transit_account:
            raise MissingError('Please Configure'
                               ' Transit Account in Company : [ {} ]'.
                               format(self.env.user.company_id.name))
        payload = {
            'name': self.description,
            'journal_id': self.journal_id.id,
            'account_id': self.env.user.company_id.transit_account.id,
            'move_id': move_id,
            'partner_id': parish_partner(self),
            'quantity': 1,
            'credit': abs(self.amount),
            'debit': 0.0,
            'date': self.date,
        }
        account_move_line = self.env['account.move.line'].with_context(
            check_move_validity=False)
        account_move_line.create(payload)

    def _prepare_second_account_move_line(self, move_id):
        if self and self.journal_id and \
                not self.journal_id.default_debit_account_id:
            raise MissingError('{} default debit and credit'
                               ' are not set.'.format(self.journal_id.name))
        payload = {
            'name': self.description,
            'account_id': self.journal_id.default_debit_account_id.id,
            'move_id': move_id,
            'partner_id': parish_partner(self),
            'quantity': 1,
            'debit': abs(self.amount),
            'credit': 0.0,
            'date': self.date,
        }
        account_move_line = self.env['account.move.line'].with_context(
            check_move_validity=False)
        account_move_line.create(payload)

    def lodge(self):
        """lodgement."""
        move = self._prepare_account_move()
        self._prepare_second_account_move_line(move.id)  # credit line
        self._prepare_first_account_move_line(move.id)  # debit line
        move.post()
        self.name = move.name
        self.state = move.state
