# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class AccountStandardLedger(models.Model):
    _name = 'account.report.template'
    _description = 'Account Standard Ledger Template'

    name = fields.Char(default='Standard Report Template')
    ledger_type = fields.Selection(
        [('general', 'Libro mayor'),
         ('partner', 'Libro mayor de socios'),
         ('journal', 'Libro mayor de diario'),
         ('open', 'Libro mayor abierto'),
         ('aged', 'Balance envejecido'),
         ('analytic', 'Libro mayor analítico')],
        string='Tipo', default='general', required=True,
        help=' * General Ledger : Journal entries group by account\n'
        ' * Partner Leger : Journal entries group by partner, with only payable/recevable accounts\n'
        ' * Journal Ledger : Journal entries group by journal, without initial balance\n'
        ' * Open Ledger : Openning journal at Start date\n')
    summary = fields.Boolean('balance de equilibrio', default=False,
                             help=' * Check : generate a trial balance.\n'
                             ' * Uncheck : detail report.\n')
    amount_currency = fields.Boolean('With Currency', help='It adds the currency column on report if the '
                                     'currency differs from the company currency.')
    reconciled = fields.Boolean(
        'Con entradas reconciliadas', default=True,
        help='Only for entrie with a payable/receivable account.\n'
        ' * Check this box to see un-reconcillied and reconciled entries with payable.\n'
        ' * Uncheck to see only un-reconcillied entries. Can be use only with parnter ledger.\n')
    partner_select_ids = fields.Many2many(
        comodel_name='res.partner', string='Socios',
        domain=['|', ('is_company', '=', True), ('parent_id', '=', False)],
        help='If empty, get all partners')
    account_methode = fields.Selection([('include', 'Incluir'), ('exclude', 'Excluir')], string="Metodo")
    account_in_ex_clude_ids = fields.Many2many(comodel_name='account.account', string='Cuentas',
                                               help='If empty, get all accounts')
    analytic_account_select_ids = fields.Many2many(comodel_name='account.analytic.account', string='Cuentas analíticas')
    init_balance_history = fields.Boolean(
        'Initial balance with history.', default=True,
        help=' * Check this box if you need to report all the debit and the credit sum before the Start Date.\n'
        ' * Uncheck this box to report only the balance before the Start Date\n')
    company_id = fields.Many2one('res.company', string='Compañia', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id',
                                          string="Compañia Moneda", readonly=True,
                                          help='Utility field to express amount currency', store=True)
    journal_ids = fields.Many2many('account.journal', string='Diarios', required=True,
                                   default=lambda self: self.env['account.journal'].search(
                                       [('company_id', '=', self.env.user.company_id.id)]),
                                   help='Select journal, for the Open Ledger you need to set all journals.')
    date_from = fields.Date(string='Fecha Inicio', help='Use to compute initial balance.')
    date_to = fields.Date(string='Fecha Fin', help='Use to compute the entrie matched with futur.')
    target_move = fields.Selection([('posted', 'Todas las entradas publicadas'),
                                    ('all', 'Todas las entradas'),
                                    ], string='Movimientos', required=True, default='posted')
    result_selection = fields.Selection([('customer', 'Clientes'),
                                         ('supplier', 'Proveedores'),
                                         ('customer_supplier', 'Customers and Suppliers')
                                         ], string="Selección de socios", required=True, default='supplier')
    report_name = fields.Char('Nombre Reporte')
    compact_account = fields.Boolean('Cuenta compacta.', default=False)

    @api.onchange('account_in_ex_clude_ids')
    def _onchange_account_in_ex_clude_ids(self):
        if self.account_in_ex_clude_ids:
            self.account_methode = 'include'
        else:
            self.account_methode = False

    @api.onchange('ledger_type')
    def _onchange_ledger_type(self):
        if self.ledger_type in ('partner', 'journal', 'open', 'aged'):
            self.compact_account = False
        if self.ledger_type == 'aged':
            self.date_from = False
            self.reconciled = False
        if self.ledger_type not in ('partner', 'aged',):
            self.reconciled = True
            return {'domain': {'account_in_ex_clude_ids': []}}
        self.account_in_ex_clude_ids = False
        if self.result_selection == 'supplier':
            return {'domain': {'account_in_ex_clude_ids': [('type_third_parties', '=', 'supplier')]}}
        if self.result_selection == 'customer':
            return {'domain': {'account_in_ex_clude_ids': [('type_third_parties', '=', 'customer')]}}
        return {'domain': {'account_in_ex_clude_ids': [('type_third_parties', 'in', ('supplier', 'customer'))]}}
