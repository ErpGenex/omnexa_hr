# Copyright (c) 2026, ErpGenEx
from frappe.tests.utils import FrappeTestCase

from omnexa_core.omnexa_core.vertical_parity import preview_for_vertical


class TestSapParitySector(FrappeTestCase):
	def test_vertical_kpi_preview(self):
		out = preview_for_vertical("hr", gross_pay=5000, deductions=500)
		self.assertEqual(out["vertical"], "hr")
		self.assertIn("kpi", out)
		self.assertIn("sap_module", out)
