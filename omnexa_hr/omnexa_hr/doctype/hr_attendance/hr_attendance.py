import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HRAttendance(Document):
	def validate(self):
		self._sync_from_employee()
		self._validate_employee_company()
		self._set_working_hours()

	def _sync_from_employee(self):
		if not self.employee:
			return
		employee = frappe.db.get_value(
			"Employee",
			self.employee,
			["company", "branch", "employee_name"],
			as_dict=True,
		)
		if not employee:
			return
		if employee.company and not self.company:
			self.company = employee.company
		if employee.branch and not self.branch:
			self.branch = employee.branch
		if employee.employee_name:
			self.employee_name = employee.employee_name

	def _validate_employee_company(self):
		if not self.employee or not self.company:
			return
		employee_company = frappe.db.get_value("Employee", self.employee, "company")
		if employee_company and employee_company != self.company:
			frappe.throw(_("Employee belongs to a different company."), title=_("Company"))
		employee_branch = frappe.db.get_value("Employee", self.employee, "branch")
		if employee_branch and self.branch and employee_branch != self.branch:
			frappe.throw(_("Employee belongs to a different branch."), title=_("Branch"))

	def _set_working_hours(self):
		if self.check_in and self.check_out:
			diff_seconds = (self.check_out - self.check_in).total_seconds()
			self.working_hours = max(flt(diff_seconds / 3600.0), 0)
