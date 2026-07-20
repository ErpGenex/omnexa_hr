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
	if filters.get("employee"):
		conditions.append("p.employee = %(employee)s")
	if filters.get("from_date"):
		conditions.append("p.payroll_month >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("p.payroll_month <= %(to_date)s")
	if filters.get("status"):
		conditions.append("p.status = %(status)s")

	data = frappe.db.sql(
		f"""
		SELECT
			p.name,
			p.employee,
			IFNULL(e.employee_name, '') AS employee_name,
			p.company,
			p.payroll_month,
			p.status,
			COALESCE(p.basic_salary, 0) AS basic_salary,
			COALESCE(p.allowances, 0) AS allowances,
			COALESCE(p.deductions, 0) AS deductions,
			COALESCE(p.bonus, 0) AS bonus,
			COALESCE(p.net_pay, 0) AS net_pay
		FROM `tabHR Payroll Entry` p
		LEFT JOIN `tabEmployee` e ON e.name = p.employee
		WHERE {' AND '.join(conditions)}
		ORDER BY p.payroll_month DESC, p.employee
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		for k in ("basic_salary", "allowances", "deductions", "bonus", "net_pay"):
			row[k] = flt(row[k])

	columns = [
		{"label": _("Payroll Entry"), "fieldname": "name", "fieldtype": "Link", "options": "HR Payroll Entry", "width": 140},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
		{"label": _("Payroll Month"), "fieldname": "payroll_month", "fieldtype": "Date", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("Basic Salary"), "fieldname": "basic_salary", "fieldtype": "Currency", "width": 120},
		{"label": _("Allowances"), "fieldname": "allowances", "fieldtype": "Currency", "width": 110},
		{"label": _("Deductions"), "fieldname": "deductions", "fieldtype": "Currency", "width": 110},
		{"label": _("Bonus"), "fieldname": "bonus", "fieldtype": "Currency", "width": 100},
		{"label": _("Net Pay"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 120},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart