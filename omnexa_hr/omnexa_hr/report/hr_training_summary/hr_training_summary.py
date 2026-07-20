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

	conditions = ["t.company = %(company)s"]
	if filters.get("from_date"):
		conditions.append("COALESCE(t.start_date, t.end_date) >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("COALESCE(t.end_date, t.start_date) <= %(to_date)s")
	if filters.get("status"):
		conditions.append("t.status = %(status)s")

	data = frappe.db.sql(
		f"""
		SELECT
			t.status,
			t.training_title,
			COUNT(t.name) AS records,
			COALESCE(SUM(t.cost), 0) AS total_cost
		FROM `tabHR Training Record` t
		WHERE {' AND '.join(conditions)}
		GROUP BY t.status, t.training_title
		ORDER BY records DESC, t.training_title
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		row.total_cost = flt(row.total_cost)

	columns = [
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 120},
		{"label": _("Training"), "fieldname": "training_title", "fieldtype": "Data", "width": 220},
		{"label": _("Records"), "fieldname": "records", "fieldtype": "Int", "width": 100},
		{"label": _("Total Cost"), "fieldname": "total_cost", "fieldtype": "Currency", "width": 120},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart