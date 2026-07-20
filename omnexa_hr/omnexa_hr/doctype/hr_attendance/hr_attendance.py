import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HRAttendance(Document):
	def validate(self):
		self._validate_employee_company()
		self._set_working_hours()

	def _validate_employee_company(self):
		if not self.employee or not self.company:
			return
		employee_company = frappe.db.get_value("Employee", self.employee, "company")
		if employee_company and employee_company != self.company:
			frappe.throw(_("Employee belongs to a different company."), title=_("Company"))

	def _set_working_hours(self):
		if self.check_in and self.check_out:
			diff_seconds = (self.check_out - self.check_in).total_seconds()
			self.working_hours = max(flt(diff_seconds / 3600.0), 0)
