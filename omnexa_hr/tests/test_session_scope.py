# Copyright (c) 2026, Omnexa
from frappe.tests.utils import FrappeTestCase


class TestWave4SessionScope(FrappeTestCase):
	def test_vertical_dashboard(self):
		from omnexa_hr.vertical_dashboard_api import get_vertical_dashboard

		out = get_vertical_dashboard()
		self.assertEqual(out.get("app"), "omnexa_hr")
		self.assertIn("uses_session_context", out)

	def test_hr_dashboard_catalog(self):
		from omnexa_hr.omnexa_hr.api.hr_dashboard import get_hr_dashboard_catalog

		out = get_hr_dashboard_catalog()
		self.assertIn("kpis", out)
