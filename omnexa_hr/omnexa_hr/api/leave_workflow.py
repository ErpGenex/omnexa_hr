# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from omnexa_core.omnexa_core.api_scope import get_api_scope
from omnexa_hr.permissions import _has_full_hr_access, get_linked_employee
from omnexa_hr.omnexa_hr.services.leave_balance import update_pending_days


@frappe.whitelist()
def get_my_employee() -> str | None:
	return get_linked_employee()


@frappe.whitelist()
def submit_leave(name: str) -> dict:
	doc = frappe.get_doc("HR Leave Application", name)
	_ensure_own_or_hr(doc)
	if doc.status not in ("Draft", ""):
		frappe.throw(_("Leave application is already submitted."), title=_("Leave"))
	doc.status = "Submitted"
	doc.flags.ignore_permissions = True
	doc.save()
	update_pending_days(doc)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_leave(name: str) -> dict:
	if not _has_full_hr_access():
		frappe.throw(_("Only HR staff can approve leave."), frappe.PermissionError)
	doc = frappe.get_doc("HR Leave Application", name)
	if doc.status != "Submitted":
		frappe.throw(_("Only submitted applications can be approved."), title=_("Leave"))
	doc.status = "Approved"
	doc.flags.ignore_permissions = True
	doc.save()
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def reject_leave(name: str, reason: str | None = None) -> dict:
	if not _has_full_hr_access():
		frappe.throw(_("Only HR staff can reject leave."), frappe.PermissionError)
	doc = frappe.get_doc("HR Leave Application", name)
	if doc.status != "Submitted":
		frappe.throw(_("Only submitted applications can be rejected."), title=_("Leave"))
	doc.status = "Rejected"
	if reason:
		doc.reason = (doc.reason or "") + f"\n[Rejected] {reason}"
	doc.flags.ignore_permissions = True
	doc.save()
	update_pending_days(doc)
	return {"name": doc.name, "status": doc.status}


def _ensure_own_or_hr(doc):
	if _has_full_hr_access():
		return
	employee = get_linked_employee()
	if employee and doc.employee != employee:
		frappe.throw(_("You can only submit your own leave application."), frappe.PermissionError)


@frappe.whitelist()
def get_ess_dashboard() -> dict:
	"""Employee self-service summary for linked user."""
	employee = get_linked_employee()
	if not employee and not _has_full_hr_access():
		return {"employee": None, "message": "No employee linked to your user"}

	if not employee and _has_full_hr_access():
		return {"employee": None, "message": "HR user — open Employee Directory"}

	emp = frappe.db.get_value(
		"Employee",
		employee,
		["name", "employee_name", "employee_code", "department", "designation", "employee_photo", "company", "branch"],
		as_dict=True,
	)

	pending_leave = frappe.db.count("HR Leave Application", {"employee": employee, "status": "Submitted"})
	approved_leave = frappe.db.count("HR Leave Application", {"employee": employee, "status": "Approved"})
	balances = frappe.get_all(
		"HR Leave Balance",
		filters={"employee": employee},
		fields=["leave_type", "balance_days", "fiscal_year"],
		limit=10,
	)

	return {
		"employee": emp,
		"pending_leave": pending_leave,
		"approved_leave": approved_leave,
		"leave_balances": balances,
		"recent_attendance": frappe.get_all(
			"HR Attendance",
			filters={"employee": employee},
			fields=["attendance_date", "status", "check_in", "check_out", "working_hours"],
			order_by="attendance_date desc",
			limit=7,
		),
		"scope": get_api_scope(),
	}
