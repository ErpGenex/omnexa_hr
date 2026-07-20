# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from frappe.utils import flt


def recompute_salary_slip_totals(doc):
	"""Roll up component lines into slip totals (employee net + P&L expense)."""
	gross = 0.0
	ded = 0.0
	employer = 0.0
	for row in doc.lines or []:
		amt = flt(row.amount)
		ctype = (row.component_type or "").strip()
		if ctype == "Deduction":
			ded += amt
		elif ctype == "Employer Contribution":
			employer += amt
		else:
			gross += amt
	doc.gross_pay = gross
	doc.total_deductions = ded
	doc.employer_contributions_total = employer
	doc.net_pay = gross - ded
	doc.expense_total = gross + employer
