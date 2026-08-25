import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class HRLeaveBalance(Document):
	def validate(self):
		self._compute_balance()
		self._validate_unique_period()

	def _compute_balance(self):
		self.balance_days = flt(self.allocated_days) - flt(self.used_days) - flt(self.pending_days)

	def _validate_unique_period(self):
		if not (self.employee and self.leave_type and self.fiscal_year):
			return
		filters = {
			"employee": self.employee,
			"leave_type": self.leave_type,
			"fiscal_year": self.fiscal_year,
			"name": ["!=", self.name or ""],
		}
		if frappe.db.exists("HR Leave Balance", filters):
			frappe.throw(_("Leave balance already exists for this employee, leave type and year."))
