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

	conditions = ["p.company = %(company)s"]
	if filters.get("from_date"):
		conditions.append("p.payroll_month >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("p.payroll_month <= %(to_date)s")
	if filters.get("status"):
		conditions.append("p.status = %(status)s")

	data = frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(p.payroll_month, '%Y-%m') AS payroll_period,
			p.status,
			COUNT(p.name) AS employees,
			COALESCE(SUM(p.basic_salary), 0) AS basic_salary,
			COALESCE(SUM(p.allowances), 0) AS allowances,
			COALESCE(SUM(p.deductions), 0) AS deductions,
			COALESCE(SUM(p.bonus), 0) AS bonus,
			COALESCE(SUM(p.net_pay), 0) AS net_pay
		FROM `tabHR Payroll Entry` p
		WHERE {' AND '.join(conditions)}
		GROUP BY DATE_FORMAT(p.payroll_month, '%Y-%m'), p.status
		ORDER BY payroll_period DESC, p.status
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		for k in ("basic_salary", "allowances", "deductions", "bonus", "net_pay"):
			row[k] = flt(row[k])

	columns = [
		{"label": _("Payroll Period"), "fieldname": "payroll_period", "fieldtype": "Data", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{"label": _("Employees"), "fieldname": "employees", "fieldtype": "Int", "width": 100},
		{"label": _("Basic Salary"), "fieldname": "basic_salary", "fieldtype": "Currency", "width": 120},
		{"label": _("Allowances"), "fieldname": "allowances", "fieldtype": "Currency", "width": 110},
		{"label": _("Deductions"), "fieldname": "deductions", "fieldtype": "Currency", "width": 110},
		{"label": _("Bonus"), "fieldname": "bonus", "fieldtype": "Currency", "width": 100},
		{"label": _("Net Pay"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 120},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart