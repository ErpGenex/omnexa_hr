# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Payroll statutory deductions register — gross, deductions, net (MVP from HR Payroll Entry)."""

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.utils.report_charts import auto_chart_for_columns
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.get("company"):
		frappe.throw(_("Company is required"))

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
			p.name,
			p.employee,
			IFNULL(e.employee_name, '') AS employee_name,
			p.payroll_month,
			p.status,
			COALESCE(p.basic_salary, 0) AS basic_salary,
			COALESCE(p.allowances, 0) AS allowances,
			COALESCE(p.bonus, 0) AS bonus,
			(COALESCE(p.basic_salary, 0) + COALESCE(p.allowances, 0) + COALESCE(p.bonus, 0)) AS gross_pay,
			COALESCE(p.deductions, 0) AS statutory_deductions,
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
		for f in ("basic_salary", "allowances", "bonus", "gross_pay", "statutory_deductions", "net_pay"):
			row[f] = flt(row[f])

	columns = [
		{"label": _("Payroll Entry"), "fieldname": "name", "fieldtype": "Link", "options": "HR Payroll Entry", "width": 130
	},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 110
	},
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150
	},
		{"label": _("Payroll Month"), "fieldname": "payroll_month", "fieldtype": "Date", "width": 110
	},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 90
	},
		{"label": _("Gross Pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 110
	},
		{"label": _("Deductions"), "fieldname": "statutory_deductions", "fieldtype": "Currency", "width": 110
	},
		{"label": _("Net Pay"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 110
	},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart