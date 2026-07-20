# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt

from omnexa_core.omnexa_core.branch_access import get_default_branch
from omnexa_core.omnexa_core.feature_flags import is_feature_enabled


def create_payroll_accrual_journal(run_doc) -> str | None:
	"""Post consolidated payroll accrual: Dr salary expense (by cost center) / Cr payroll liability."""
	if not is_feature_enabled("global_hr_payroll_auto_accrual_je", True):
		return None
	if not frappe.db.exists("DocType", "Journal Entry"):
		return None

	company = run_doc.company
	settings_name = frappe.db.get_value("HR Payroll Company Settings", {"company": company
	}, "name")
	if not settings_name:
		frappe.throw(
			_("Create HR Payroll Company Settings for company {0} before submitting a payroll run.").format(company),
			title=_("Payroll Settings"),
		)
	settings = frappe.get_doc("HR Payroll Company Settings", settings_name)
	expense_acc = settings.salary_expense_account
	liability_acc = settings.payroll_liability_account
	if not expense_acc or not liability_acc:
		frappe.throw(_("Salary expense and payroll liability GL accounts are required."), title=_("Payroll Settings"))

	branch = (
		run_doc.branch
		or settings.default_branch
		or get_default_branch(company)
		or frappe.db.get_value("Branch", {"company": company
	}, "name")
	)
	if not branch:
		frappe.throw(_("Branch is required to post payroll accrual journal."), title=_("Branch"))

	by_cc: dict[str, float] = defaultdict(float)
	for row in run_doc.lines or []:
		if not row.salary_slip:
			continue
		slip = frappe.get_doc("HR Salary Slip", row.salary_slip)
		cc = (
			frappe.db.get_value("Employee", slip.employee, "hr_default_cost_center") or run_doc.cost_center or ""
		).strip()
		by_cc[cc] += flt(slip.expense_total)

	total_expense = sum(by_cc.values())
	if total_expense <= 0:
		frappe.throw(_("Total payroll expense must be greater than zero."), title=_("Payroll Run"))

	accounts = []
	for cc, amt in sorted(by_cc.items(), key=lambda x: x[0]):
		if flt(amt) <= 0:
			continue
		line = {"account": expense_acc, "debit": flt(amt, 2), "credit": 0
	}
		if cc:
			line["cost_center"] = cc
		accounts.append(line)

	total_debit = sum(flt(a.get("debit") or 0) for a in accounts)
	accounts.append({"account": liability_acc, "debit": 0, "credit": flt(total_debit, 2)})

	je = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"company": company,
			"branch": branch,
			"posting_date": run_doc.posting_date,
			"entry_type": "Standard",
			"reference": run_doc.name,
			"remarks": _("Payroll accrual — period {0} to {1}").format(run_doc.period_start, run_doc.period_end),
			"accounts": accounts
	}
	)
	je.insert(ignore_permissions=True)
	je.submit()
	return je.name
