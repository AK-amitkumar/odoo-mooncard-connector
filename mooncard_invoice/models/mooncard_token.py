# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class MooncardToken(models.Model):
    _inherit = 'mooncard.token'

    journal_id = fields.Many2one(
        'account.journal', string='Mooncard Bank Journal',
        domain=[('type', '=', 'bank')])
