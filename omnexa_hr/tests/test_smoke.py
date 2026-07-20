from frappe.tests.utils import FrappeTestCase

from omnexa_hr import hooks


class TestHRSmoke(FrappeTestCase):
	def test_hooks_are_present(self):
		self.assertEqual(hooks.app_name, "omnexa_hr")
		self.assertIn("omnexa_core", hooks.required_apps)

