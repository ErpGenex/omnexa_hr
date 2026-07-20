# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["a.company = %(company)s"]
	if filters.get("from_date"):
		conditions.append("a.attendance_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("a.attendance_date <= %(to_date)s")
	if filters.get("status"):
		conditions.append("a.status = %(status)s")

	data = frappe.db.sql(
		f"""
		SELECT
			a.attendance_date,
			a.status,
			COUNT(a.name) AS records
		FROM `tabHR Attendance` a
		WHERE {' AND '.join(conditions)}
		GROUP BY a.attendance_date, a.status
		ORDER BY a.attendance_date DESC, a.status
		""",
		filters,
		as_dict=True,
	)

	columns = [
		{"label": _("Date"), "fieldname": "attendance_date", "fieldtype": "Date", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Records"), "fieldname": "records", "fieldtype": "Int", "width": 100},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart