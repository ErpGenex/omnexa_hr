import frappe
from frappe.model.document import Document


class HRBiometricDevice(Document):
	def validate(self):
		if self.device_port and int(self.device_port) <= 0:
			frappe.throw("Device port must be positive.")
