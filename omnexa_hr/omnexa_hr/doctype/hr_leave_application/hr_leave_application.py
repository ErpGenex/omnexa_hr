import frappe
from frappe import _
from frappe.model.document import Document

from omnexa_hr.omnexa_hr.services.leave_balance import apply_approved_leave, update_pending_days


class HRLeaveApplication(Document):
	def validate(self):
		if self.from_date and self.to_date and self.to_date < self.from_date:
			frappe.throw(_("To date cannot be before from date."), title=_("Leave Application"))

		if self.from_date and self.to_date:
			days = frappe.utils.date_diff(self.to_date, self.from_date) + 1
			self.total_days = float(days)

		if self.employee and not self.company:
			self.company = frappe.db.get_value("Employee", self.employee, "company")
		if self.employee and not self.branch:
			self.branch = frappe.db.get_value("Employee", self.employee, "branch")

	def on_update(self):
		update_pending_days(self)
		prev = self.get_doc_before_save()
		prev_status = prev.status if prev else None
		if self.status == "Approved" and prev_status != "Approved":
			apply_approved_leave(self)
