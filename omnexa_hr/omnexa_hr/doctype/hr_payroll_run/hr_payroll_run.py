# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from omnexa_accounting.utils.branch import validate_branch_company

from omnexa_hr.omnexa_hr.payroll.accounting import create_payroll_accrual_journal


class HRPayrollRun(Document):
	def validate(self):
		validate_branch_company(self)
		self._validate_lines()

	def _validate_lines(self):
		for row in self.lines or []:
			if not row.salary_slip:
				continue
			slip = frappe.db.get_value(
				"HR Salary Slip",
				row.salary_slip,
				["docstatus", "company", "period_start", "period_end"],
				as_dict=True,
			)
			if not slip:
				frappe.throw(_("Row {0}: Salary Slip not found.").format(row.idx), title=_("Payroll Run"))
			if slip.docstatus != 1:
				frappe.throw(_("Row {0}: Salary Slip must be submitted.").format(row.idx), title=_("Payroll Run"))
			if slip.company != self.company:
				frappe.throw(_("Row {0}: Salary Slip company mismatch.").format(row.idx), title=_("Company"))

	def on_submit(self):
		je = create_payroll_accrual_journal(self)
		if je:
			self.db_set("accrual_journal_entry", je, update_modified=False)
