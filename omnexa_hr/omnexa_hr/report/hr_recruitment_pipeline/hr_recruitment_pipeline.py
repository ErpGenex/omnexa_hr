# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["r.company = %(company)s"]
	if filters.get("from_date"):
		conditions.append("r.request_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("r.request_date <= %(to_date)s")
	if filters.get("status"):
		conditions.append("r.status = %(status)s")

	data = frappe.db.sql(
		f"""
		SELECT
			r.status,
			r.department,
			SUM(r.open_positions) AS open_positions,
			COUNT(r.name) AS requests
		FROM `tabHR Recruitment Request` r
		WHERE {' AND '.join(conditions)}
		GROUP BY r.status, r.department
		ORDER BY open_positions DESC, r.department
		""",
		filters,
		as_dict=True,
	)

	columns = [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 180},
		{"label": _("Open Positions"), "fieldname": "open_positions", "fieldtype": "Int", "width": 130},
		{"label": _("Requests"), "fieldname": "requests", "fieldtype": "Int", "width": 100},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart