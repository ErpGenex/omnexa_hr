import frappe
from frappe.model.document import Document
from frappe.utils import flt


class HRExpenseClaim(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw("Amount must be greater than zero.")
		if self.expense_date and self.posting_date and self.expense_date > self.posting_date:
			frappe.throw("Expense date cannot be after posting date.")
