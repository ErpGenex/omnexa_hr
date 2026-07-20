# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from omnexa_accounting.utils.branch import validate_branch_company


class HRSalaryAdvance(Document):
	def validate(self):
		validate_branch_company(self)
		if self.employee:
			emp_co = frappe.db.get_value("Employee", self.employee, "company")
			if emp_co and self.company and emp_co != self.company:
				frappe.throw(_("Employee belongs to a different company."), title=_("Company"))
		out = flt(self.amount) - flt(self.recovered_amount)
		self.outstanding = max(out, 0)
		if flt(self.recovered_amount) > flt(self.amount):
			frappe.throw(_("Recovered cannot exceed advance amount."), title=_("Salary Advance"))
