# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HRPayrollCompanySettings(Document):
	def validate(self):
		for fname in (
			"salary_expense_account",
			"employer_benefits_expense_account",
			"payroll_liability_account",
			"payroll_tax_payable_account",
			"salary_advance_clearing_account",
			"eos_provision_account",
		):
			acc = self.get(fname)
			if not acc:
				continue
			cc = frappe.db.get_value("GL Account", acc, "company")
			if cc and cc != self.company:
				frappe.throw(
					_("{0}: GL Account belongs to another company.").format(_(fname)),
					title=_("GL Account"),
				)
