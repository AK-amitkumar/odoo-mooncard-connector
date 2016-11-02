# -*- coding: utf-8 -*-
# © 2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
from openerp.tools import float_compare


class TestMooncardInvoice(TransactionCase):

    def setUp(self):
        super(TestMooncardInvoice, self).setUp()
        self.account_model = self.env['account.account']
        self.move_model = self.env['account.move']
        self.journal_model = self.env['account.journal']
        bank_type = self.env.ref('account.data_account_type_bank')
        baccounts = self.account_model.search(
            [('user_type', '=', bank_type.id)])
        self.moon_bank_account = self.account_model.create({
            'parent_id': baccounts[0].parent_id.id,
            'code': '512199',
            'name': 'Mooncard prepaid account',
            'user_type': bank_type.id,
            'type': 'liquidity',
            })
        self.moon_bank_journal = self.journal_model.create({
            'type': 'bank',
            'name': 'MoonCard Test',
            'code': 'MOON',
            'default_debit_account_id': self.moon_bank_account.id,
            'default_credit_account_id': self.moon_bank_account.id,
            })
        self.card1 = self.env.ref('mooncard_base.card1')
        self.card1.write({
            'journal_id': self.moon_bank_journal.id})
        accounts = self.account_model.search(
            [('reconcile', '=', True), ('type', '=', 'other')])
        self.company = self.env.ref('base.main_company')
        self.euro = self.env.ref('base.EUR')
        self.company.write({
            'transfer_account_id': accounts[0].id,
            'currency_id': self.euro.id,
            })
        self.prec = self.env['decimal.precision'].precision_get('Account')

    def test_load_line(self):
        # Set company country to France
        load1 = self.env.ref('mooncard_base.load1')
        load1.process_line()
        self.assertEqual(load1.state, 'done')
        self.assertTrue(load1.load_move_id)
        self.assertEqual(load1.load_move_id.journal_id, self.card1.journal_id)
        self.assertEqual(load1.load_move_id.date, load1.date[:10])

    def test_expense_line(self):
        for expense_xmlid in ['expense1', 'expense2', 'expense3']:
            expense = self.env.ref('mooncard_base.%s' % expense_xmlid)
            expense.process_line()
            self.assertEqual(expense.state, 'done')
            inv = expense.invoice_id
            self.assertEqual(inv.state, 'paid')
            if float_compare(
                    expense.total_company_currency, 0,
                    precision_digits=self.prec) == -1:
                self.assertEqual(inv.type, 'in_invoice')
            else:
                self.assertEqual(inv.type, 'in_refund')
            self.assertFalse(float_compare(
                abs(expense.total_company_currency),
                inv.amount_total,
                precision_digits=self.prec))
            self.assertFalse(float_compare(
                abs(expense.vat_company_currency),
                inv.amount_tax,
                precision_digits=self.prec))
            self.assertEqual(inv.date_invoice, expense.date[:10])
            pay_move_line = expense.payment_move_line_id
            self.assertTrue(pay_move_line)
            self.assertEqual(pay_move_line.date, expense.date[:10])
            self.assertEqual(pay_move_line.journal_id, self.card1.journal_id)
            self.assertTrue(expense.reconcile_id)
