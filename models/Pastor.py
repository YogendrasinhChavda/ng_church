# *-* coding:utf-8 -*-
"""Ng Church Pastor Model."""
import re
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class Pastor(models.Model):
    """Ng Church Pastor Model."""

    _name = 'ng_church.pastor'
    _description = 'Church Pastor'

    pastor_harachies = [
        ('Assistant Pastor in Charge of Parish',
         'Assistant Pastor in Charge of Parish'),
        ('Pastors in Charge of Parish', 'Pastors in Charge of Parish'),
        ('Pastors in Charge of Area', 'Pastors in Charge of Area'),
        ('Pastors in Charge of Zone', 'Pastors in Charge of Zone'),
        ('Assistant Pastors in Charge of Province',
         'Assistant Pastors in Charge of Province'),
        ('Pastors in Charge of Province', 'Pastors in Charge of Province'),
        ('Pastors in Charge of Region', 'Pastors in Charge of Region')
    ]
    minister_position = [('minister', 'Minister')]
    minister = [('minister', 'Minister'), ('pastor', 'Pastor')]
    type_of_minister = fields.Selection(selection=minister, required=True,
                                        default='minister')
    name = fields.Char(string='First Name')
    lastname = fields.Char(string='Last Name')
    users_id = fields.Many2one('res.users', string='User\'s Name',
                               required=True)
    pastor_hierarchy = fields.Selection(selection=pastor_harachies,
                                        string='Pastor Position')
    lead_pastor = fields.Boolean(string='Lead Pastor')
    minister_hierarchy = fields.Selection(selection=minister_position,
                                          string='Position',
                                          default='minister')
    home_address = fields.Char(string='Address')
    personal_email = fields.Char(string='Email', required=True)
    personal_phone = fields.Char(string='Phone')
    church_id = fields.Many2one('res.company', string='Church')
    date_of_birth = fields.Date(string='Date of Birth')
    is_born_again = fields.Boolean(string="Born again")
    born_again_date = fields.Date(string='Born Again Date')
    is_spirit_filled = fields.Boolean(string="Spirit Filled")
    spirit_filled_date = fields.Date(string='Spirit Filled Date')

    @api.constrains('personal_email')
    def _check_valid_email(self):
        """Method to check phone validation."""
        result = re.compile(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
        for ng_pastor in self:
            if result.match(ng_pastor.personal_email) is None:
                raise ValidationError('Please enter a valid email address')

    @api.constrains('personal_phone')
    def _check_valid_phone(self, limit=11):
        """Method to check phone validation."""
        for ng_pastor in self:
            if ng_pastor.personal_phone:
                if len(ng_pastor.personal_phone) > 11:
                    raise ValidationError('Please enter a valid phone number')
                result = re.compile(r"\d{11}")
                if result.match(ng_pastor.personal_phone) is None:
                    raise ValidationError('Please enter a valid phone number')
