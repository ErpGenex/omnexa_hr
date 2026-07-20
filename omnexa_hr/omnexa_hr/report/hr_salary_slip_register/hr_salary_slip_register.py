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

	conditions = ["s.company = %(company)s"]
	if filters.get("employee"):
		conditions.append("s.employee = %(employee)s")
	if filters.get("from_date"):
		conditions.append("s.period_start >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("s.period_end <= %(to_date)s")
	if filters.get("docstatus") not in (None, ""):
		conditions.append("s.docstatus = %(docstatus)s")

	data = frappe.db.sql(
		f"""
		SELECT
			s.name,
			s.employee,
			IFNULL(s.employee_name, e.employee_name) AS employee_name,
			s.company,
			s.branch,
			s.period_start,
			s.period_end,
			s.posting_date,
			s.docstatus,
			COALESCE(s.gross_pay, 0) AS gross_pay,
			COALESCE(s.total_deductions, 0) AS total_deductions,
			COALESCE(s.employer_contributions_total, 0) AS employer_contributions_total,
			COALESCE(s.net_pay, 0) AS net_pay,
			COALESCE(s.expense_total, 0) AS expense_total
		FROM `tabHR Salary Slip` s
		LEFT JOIN `tabEmployee` e ON e.name = s.employee
		WHERE {' AND '.join(conditions)}
		ORDER BY s.period_end DESC, s.employee
		""",
		filters,
		as_dict=True,
	)
	for row in data:
		for k in (
			"gross_pay",
			"total_deductions",
			"employer_contributions_total",
			"net_pay",
			"expense_total",
		):
			row[k] = flt(row[k])

	columns = [
		{"label": _("Salary Slip"), "fieldname": "name", "fieldtype": "Link", "options": "HR Salary Slip", "width": 150},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 120},
		{"label": _("Branch"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 120},
		{"label": _("Period Start"), "fieldname": "period_start", "fieldtype": "Date", "width": 110},
		{"label": _("Period End"), "fieldname": "period_end", "fieldtype": "Date", "width": 110},
		{"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 110},
		{"label": _("Docstatus"), "fieldname": "docstatus", "fieldtype": "Int", "width": 80},
		{"label": _("Gross pay"), "fieldname": "gross_pay", "fieldtype": "Currency", "width": 110},
		{"label": _("Deductions"), "fieldname": "total_deductions", "fieldtype": "Currency", "width": 110},
		{"label": _("Employer contrib."), "fieldname": "employer_contributions_total", "fieldtype": "Currency", "width": 120},
		{"label": _("Net pay"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 110},
		{"label": _("Expense (P&L)"), "fieldname": "expense_total", "fieldtype": "Currency", "width": 120},
	]
	chart = auto_chart_for_columns(data, columns)
	return columns, data, None, chart