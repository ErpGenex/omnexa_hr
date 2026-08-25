import frappe
from frappe import _
from frappe.model.document import Document


class HRDepartment(Document):
	def validate(self):
		if self.parent_department and self.parent_department == self.name:
			frappe.throw(_("Department cannot report to itself."), title=_("HR Department"))
