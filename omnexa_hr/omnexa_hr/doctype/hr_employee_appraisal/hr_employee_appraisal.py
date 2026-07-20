import frappe
from frappe.model.document import Document
from frappe.utils import flt


class HREmployeeAppraisal(Document):
	def validate(self):
		if self.review_period_end and self.review_period_start:
			if self.review_period_end < self.review_period_start:
				frappe.throw("Review period end cannot be before start.")
		for field in ("overall_score", "goals_score", "competency_score"):
			val = flt(getattr(self, field, 0))
			if val and (val < 0 or val > 100):
				frappe.throw(f"{field.replace('_', ' ').title()} must be between 0 and 100.")
