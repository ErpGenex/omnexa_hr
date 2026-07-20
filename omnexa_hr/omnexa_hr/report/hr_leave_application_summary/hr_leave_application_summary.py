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

	conditions = ["l.company = %(company)s"]
	if filters.get("branch"):
		conditions.append("l.branch = %(branch)s")
	if filters.get("from_date"):
		conditions.append("l.from_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("l.to_date <= %(to_date)s")
	if filters.get("status"):
		conditions.append("l.status = %(status)s")

	data = frappe.db.sql(
		f"""
		SELECT
			l.status,
			l.leave_type,
			l.branch,
			COUNT(l.name) AS applications,
			COALESCE(SUM(l.total_days), 0) AS total_days
		FROM `tabHR Leave Application` l
		WHERE {' AND '.join(conditions)}
		GROUP BY l.status, l.leave_type, l.branch
		ORDER BY applications DESC
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.total_days = flt(row.total_days)

	columns = [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Leave Type"), "fieldname": "leave_type", "fieldtype": "Link", "options": "HR Leave Type", "width": 160},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 130},
		{"label": _("Applications"), "fieldname": "applications", "fieldtype": "Int", "width": 120},
		{"label": _("Total Days"), "fieldname": "total_days", "fieldtype": "Float", "width": 110},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart