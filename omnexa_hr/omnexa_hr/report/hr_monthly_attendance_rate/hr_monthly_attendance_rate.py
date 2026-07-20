# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required."), title=_("Filters"))

	conditions = ["a.company = %(company)s"]
	if filters.get("from_date"):
		conditions.append("a.attendance_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("a.attendance_date <= %(to_date)s")

	data = frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(a.attendance_date, '%%Y-%%m') AS period,
			COUNT(*) AS total_records,
			SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_count,
			SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) AS absent_count,
			SUM(CASE WHEN a.status = 'Remote' THEN 1 ELSE 0 END) AS remote_count,
			SUM(CASE WHEN a.status = 'On Leave' THEN 1 ELSE 0 END) AS on_leave_count
		FROM `tabHR Attendance` a
		WHERE {' AND '.join(conditions)}
		GROUP BY DATE_FORMAT(a.attendance_date, '%%Y-%%m')
		ORDER BY period DESC
		""",
		filters,
		as_dict=True,
	)

	for row in data:
		total = int(row.total_records or 0)
		productive = int(row.present_count or 0) + int(row.remote_count or 0)
		row["productive_rate_pct"] = flt(100.0 * productive / total, 2) if total else 0.0

	columns = [
		{"label": _("Period (YYYY-MM)"), "fieldname": "period", "fieldtype": "Data", "width": 110},
		{"label": _("Total Records"), "fieldname": "total_records", "fieldtype": "Int", "width": 110},
		{"label": _("Present"), "fieldname": "present_count", "fieldtype": "Int", "width": 90},
		{"label": _("Remote"), "fieldname": "remote_count", "fieldtype": "Int", "width": 90},
		{"label": _("Absent"), "fieldname": "absent_count", "fieldtype": "Int", "width": 90},
		{"label": _("On Leave"), "fieldname": "on_leave_count", "fieldtype": "Int", "width": 90},
		{
			"label": _("Productive attendance %"),
			"fieldname": "productive_rate_pct",
			"fieldtype": "Float",
			"width": 150,
		},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart