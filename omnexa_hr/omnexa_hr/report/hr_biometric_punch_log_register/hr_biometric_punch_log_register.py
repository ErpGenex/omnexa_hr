# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `device`, `company`, `branch`, `employee`, `raw_user_id`
		FROM `tabHR Biometric Punch Log`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Biometric Device"), "fieldname": "device", "fieldtype": "Link", "width": 120},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "width": 120},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "width": 120},
		{"label": _("Raw User ID"), "fieldname": "raw_user_id", "fieldtype": "Data", "width": 120}
	]
	return columns, data
