from frappe.model.document import Document
from frappe.utils import flt


class HRPayrollEntry(Document):
	def validate(self):
		self.net_pay = flt(self.basic_salary) + flt(self.allowances) + flt(self.bonus) - flt(self.deductions)
