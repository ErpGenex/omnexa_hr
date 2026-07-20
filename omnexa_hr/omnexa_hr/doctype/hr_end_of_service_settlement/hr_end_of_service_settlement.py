# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

from omnexa_accounting.utils.branch import validate_branch_company

from omnexa_hr.omnexa_hr.payroll.eos import compute_gratuity


class HREndofServiceSettlement(Document):
	def validate(self):
		validate_branch_company(self)
		if self.employee:
			emp_co = frappe.db.get_value("Employee", self.employee, "company")
			if emp_co and self.company and emp_co != self.company:
				frappe.throw(_("Employee belongs to a different company."), title=_("Company"))
		joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")
		if joining and self.termination_date:
			td = getdate(self.termination_date)
			jd = getdate(joining)
			if td < jd:
				frappe.throw(_("Termination cannot be before joining."), title=_("EOS"))
			self.service_days = (td - jd).days
		else:
			self.service_days = 0
		daily = flt(self.last_basic_salary) / 30.0 if flt(self.last_basic_salary) else 0
		scheme = self.scheme or "GENERIC_LIMITED"
		self.gratuity_amount = compute_gratuity(
			service_days=int(self.service_days or 0),
			daily_wage=daily,
			monthly_salary=flt(self.last_basic_salary),
			scheme=scheme,
		)
