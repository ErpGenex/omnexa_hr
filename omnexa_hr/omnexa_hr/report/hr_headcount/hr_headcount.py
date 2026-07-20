# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns


def execute(filters=None):
	filters = frappe._dict(filters or {})

	columns = [
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 180},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Data", "width": 150},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Headcount"), "fieldname": "headcount", "fieldtype": "Int", "width": 120},
	]

	conditions = ["1=1"]
	params = {}

	if filters.get("company"):
		conditions.append("e.company = %(company)s")
		params["company"] = filters.company

	if filters.get("department"):
		conditions.append("e.department = %(department)s")
		params["department"] = filters.department

	if filters.get("status"):
		conditions.append("e.status = %(status)s")
		params["status"] = filters.status

	data = frappe.db.sql(
		f"""
		SELECT
			e.company,
			IFNULL(NULLIF(TRIM(e.department), ''), 'Unassigned') AS department,
			COALESCE(e.status, 'Unknown') AS status,
			COUNT(e.name) AS headcount
		FROM `tabEmployee` e
		WHERE {" AND ".join(conditions)}
		GROUP BY e.company, IFNULL(NULLIF(TRIM(e.department), ''), 'Unassigned'), e.status
		ORDER BY e.company, department, e.status
		""",
		params,
		as_dict=True,
	)
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart