# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime


def get_fiscal_year(for_date=None) -> str:
	for_date = getdate(for_date or frappe.utils.today())
	start_month = int(frappe.db.get_single_value("HR Settings", "fiscal_year_start_month") or 1)
	year = for_date.year
	if for_date.month < start_month:
		year -= 1
	return str(year)


def get_or_create_balance(employee: str, leave_type: str, company: str, branch: str | None = None):
	fiscal_year = get_fiscal_year()
	name = frappe.db.get_value(
		"HR Leave Balance",
		{"employee": employee, "leave_type": leave_type, "fiscal_year": fiscal_year},
	)
	if name:
		return frappe.get_doc("HR Leave Balance", name)

	max_days = frappe.db.get_value("HR Leave Type", leave_type, "max_days_per_year") or 0
	doc = frappe.get_doc(
		{
			"doctype": "HR Leave Balance",
			"employee": employee,
			"company": company,
			"branch": branch,
			"leave_type": leave_type,
			"fiscal_year": fiscal_year,
			"allocated_days": flt(max_days),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


def update_pending_days(leave_application):
	if leave_application.status not in ("Submitted", "Approved"):
		return
	balance = get_or_create_balance(
		leave_application.employee,
		leave_application.leave_type,
		leave_application.company,
		leave_application.branch,
	)
	pending = frappe.db.sql(
		"""
		SELECT COALESCE(SUM(total_days), 0)
		FROM `tabHR Leave Application`
		WHERE employee = %s AND leave_type = %s AND status = 'Submitted' AND name != %s
		""",
		(leave_application.employee, leave_application.leave_type, leave_application.name or ""),
	)[0][0]
	if leave_application.status == "Submitted":
		pending = flt(pending) + flt(leave_application.total_days)
	frappe.db.set_value("HR Leave Balance", balance.name, "pending_days", pending, update_modified=False)
	balance.reload()
	balance._compute_balance()
	frappe.db.set_value("HR Leave Balance", balance.name, "balance_days", balance.balance_days, update_modified=False)


def apply_approved_leave(leave_application):
	settings = frappe.get_single("HR Settings")
	if not cint(settings.enforce_leave_balance):
		return

	balance = get_or_create_balance(
		leave_application.employee,
		leave_application.leave_type,
		leave_application.company,
		leave_application.branch,
	)
	days = flt(leave_application.total_days)
	if balance.balance_days < days:
		frappe.throw(
			_("Insufficient leave balance. Available: {0}, Requested: {1}").format(balance.balance_days, days),
			title=_("Leave Balance"),
		)

	used = flt(balance.used_days) + days
	pending = flt(balance.pending_days) - days
	if pending < 0:
		pending = 0
	balance_days = flt(balance.allocated_days) - used - pending
	frappe.db.set_value(
		"HR Leave Balance",
		balance.name,
		{"used_days": used, "pending_days": pending, "balance_days": balance_days},
		update_modified=True,
	)
