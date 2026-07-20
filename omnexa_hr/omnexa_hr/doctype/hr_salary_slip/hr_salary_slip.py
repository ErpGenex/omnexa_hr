# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.model.document import Document

from omnexa_accounting.utils.branch import validate_branch_company

from omnexa_hr.omnexa_hr.payroll.attendance_gate import validate_attendance_for_salary_slip
from omnexa_hr.omnexa_hr.payroll.engine import recompute_salary_slip_totals


class HRSalarySlip(Document):
	def validate(self):
		if self.employee:
			emp_co = frappe.db.get_value("Employee", self.employee, "company")
			if emp_co and self.company and emp_co != self.company:
				frappe.throw(frappe._("Employee belongs to a different company."), title=frappe._("Company"))
		validate_branch_company(self)
		recompute_salary_slip_totals(self)

	def before_submit(self):
		validate_attendance_for_salary_slip(self)
