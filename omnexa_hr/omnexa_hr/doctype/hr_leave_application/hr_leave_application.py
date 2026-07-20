import frappe
from frappe.model.document import Document


class HRLeaveApplication(Document):
	def validate(self):
		if self.from_date and self.to_date and self.to_date < self.from_date:
			frappe.throw("To date cannot be before from date.")

		if self.from_date and self.to_date:
			days = frappe.utils.date_diff(self.to_date, self.from_date) + 1
			self.total_days = float(days)

