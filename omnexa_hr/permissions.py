# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

from __future__ import annotations

import frappe
from frappe import _

from omnexa_core.omnexa_core.branch_access import enforce_branch_access, user_can_access_all_branches
from omnexa_core.omnexa_core.user_context import apply_company_branch_defaults

HR_FULL_ACCESS_ROLES = frozenset(
	{
		"System Manager",
		"Company Admin",
		"HR Manager",
		"HR User",
		"Accounts Manager",
	}
)

HR_ESS_DOCTYPES = frozenset(
	{
		"HR Leave Application",
		"HR Attendance",
		"HR Salary Slip",
		"HR Training Record",
		"HR Employee Appraisal",
	}
)


def enforce_branch_access_for_doc(doc, method=None):
	enforce_branch_access(doc)


def populate_company_branch_from_user_context(doc, method=None):
	apply_company_branch_defaults(doc)


def _user_roles(user: str | None = None) -> set[str]:
	user = user or frappe.session.user
	return set(frappe.get_roles(user))


def _has_full_hr_access(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(_user_roles(user) & HR_FULL_ACCESS_ROLES)


def get_linked_employee(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if frappe.db.has_column("Employee", "linked_user"):
		emp = frappe.db.get_value("Employee", {"linked_user": user, "status": "Active"}, "name")
		if emp:
			return emp
	return None


def _employee_scope_sql(doctype: str, employee_field: str = "employee", user: str | None = None) -> str:
	"""Restrict HR Employee role to own records."""
	user = user or frappe.session.user
	if _has_full_hr_access(user):
		return ""
	if "HR Employee" not in _user_roles(user):
		return ""

	employee = get_linked_employee(user)
	if not employee:
		return "1=0"

	table = frappe.utils.get_table_name(doctype, wrap_in_backticks=True)
	return f"{table}.{employee_field} = {frappe.db.escape(employee)}"


def hr_leave_application_query(user=None):
	return _employee_scope_sql("HR Leave Application", user=user)


def hr_attendance_query(user=None):
	return _employee_scope_sql("HR Attendance", user=user)


def hr_salary_slip_query(user=None):
	return _employee_scope_sql("HR Salary Slip", user=user)


def hr_training_record_query(user=None):
	return _employee_scope_sql("HR Training Record", user=user)


def hr_employee_appraisal_query(user=None):
	return _employee_scope_sql("HR Employee Appraisal", user=user)


def has_hr_employee_permission(doc, ptype, user=None):
	user = user or frappe.session.user
	if _has_full_hr_access(user):
		return True
	if "HR Employee" not in _user_roles(user):
		return None

	employee = get_linked_employee(user)
	if not employee:
		return False

	doc_employee = doc.get("employee") if hasattr(doc, "get") else None
	if doc_employee and doc_employee != employee:
		return False

	if ptype == "create":
		return doc.doctype in HR_ESS_DOCTYPES
	if ptype in ("read", "write"):
		return True
	if ptype == "submit" and doc.doctype == "HR Leave Application":
		return doc.get("status") in ("Draft", "Submitted") and doc.get("employee") == employee
	return False


def validate_leave_application_permissions(doc, method=None):
	"""Only HR roles can approve/reject; employees can only draft/submit own."""
	if _has_full_hr_access():
		return
	if "HR Employee" not in _user_roles():
		return

	employee = get_linked_employee()
	if employee and doc.employee and doc.employee != employee:
		frappe.throw(_("You can only manage your own leave applications."), frappe.PermissionError)
	if doc.status in ("Approved", "Rejected") and not _has_full_hr_access():
		frappe.throw(_("Only HR staff can approve or reject leave."), frappe.PermissionError)
