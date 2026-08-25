# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from omnexa_core.omnexa_core.branch_access import get_default_branch

SUPPORTED_FRAPPE_MAJOR = 15

HR_ROLES = (
	("HR Manager", "Manages all HR operations for assigned companies/branches."),
	("HR User", "Processes HR transactions (attendance, leave, payroll)."),
	("HR Employee", "Self-service access to own HR records."),
)


def enforce_supported_frappe_version():
	"""Fail early when running on an unsupported Frappe major release."""
	version_text = (getattr(frappe, "__version__", "") or "").strip()
	if not version_text:
		return

	major_token = version_text.split(".", 1)[0]
	try:
		major = int(major_token)
	except ValueError:
		return

	if major != SUPPORTED_FRAPPE_MAJOR:
		frappe.throw(
			f"Unsupported Frappe version '{version_text}' for omnexa_hr. "
			"Supported range is >=15.0,<16.0.",
			frappe.ValidationError,
		)


def after_migrate():
	enforce_supported_frappe_version()
	ensure_hr_custom_fields()
	ensure_hr_roles()
	backfill_employee_branch()
	sync_hr_workspace()


def ensure_hr_roles():
	for role_name, description in HR_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		doc = frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1})
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Role", role_name, "description", description, update_modified=False)


def backfill_employee_branch():
	if not frappe.db.exists("DocType", "Employee"):
		return
	if not frappe.db.has_column("Employee", "branch"):
		return

	employees = frappe.get_all(
		"Employee",
		filters={"branch": ["in", ["", None]]},
		fields=["name", "company"],
		limit=5000,
	)
	for row in employees:
		if not row.company:
			continue
		branch = get_default_branch(row.company) or frappe.db.get_value(
			"Branch", {"company": row.company}, "name"
		)
		if branch:
			frappe.db.set_value("Employee", row.name, "branch", branch, update_modified=False)


def sync_hr_workspace():
	try:
		from omnexa_hr.workspace.hr_workspace import sync_hr_workspace_menu

		sync_hr_workspace_menu()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa HR: sync_hr_workspace_menu")


def ensure_hr_custom_fields():
	"""Non-destructive HR enterprise fields on Employee and legacy payroll row."""
	try:
		custom_fields_map: dict = {}

		if frappe.db.exists("DocType", "Employee"):
			employee_fields = []

			if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "branch"}):
				employee_fields.append(
					{
						"fieldname": "branch",
						"label": "Branch",
						"fieldtype": "Link",
						"options": "Branch",
						"insert_after": "company",
						"in_list_view": 1,
						"reqd": 0,
					}
				)

			if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "employee_name_ar"}):
				employee_fields.extend(
					[
						{
							"fieldname": "hr_identity_section",
							"label": "HR Identity",
							"fieldtype": "Section Break",
							"insert_after": "employee_name",
						},
						{
							"fieldname": "employee_name_ar",
							"label": "Employee Name (Arabic)",
							"fieldtype": "Data",
							"insert_after": "hr_identity_section",
						},
						{
							"fieldname": "national_id",
							"label": "National ID",
							"fieldtype": "Data",
							"insert_after": "employee_name_ar",
						},
						{
							"fieldname": "passport_number",
							"label": "Passport Number",
							"fieldtype": "Data",
							"insert_after": "national_id",
						},
						{
							"fieldname": "employment_type",
							"label": "Employment Type",
							"fieldtype": "Select",
							"options": "Full-time\nPart-time\nContract\nFreelancer\nIntern",
							"insert_after": "passport_number",
						},
						{
							"fieldname": "hr_default_cost_center",
							"label": "Default Cost Center (payroll)",
							"fieldtype": "Link",
							"options": "Cost Center",
							"insert_after": "department",
						},
						{
							"fieldname": "hr_department",
							"label": "HR Department",
							"fieldtype": "Link",
							"options": "HR Department",
							"insert_after": "designation",
						},
						{
							"fieldname": "reports_to",
							"label": "Reports To",
							"fieldtype": "Link",
							"options": "Employee",
							"insert_after": "manager",
						},
						{
							"fieldname": "salary_bank_account_no",
							"label": "Salary Bank Account No.",
							"fieldtype": "Data",
							"insert_after": "external_reference",
						},
						{
							"fieldname": "salary_iban",
							"label": "Salary IBAN",
							"fieldtype": "Data",
							"insert_after": "salary_bank_account_no",
						},
						{
							"fieldname": "biometric_user_id",
							"label": "Biometric User ID",
							"fieldtype": "Data",
							"insert_after": "salary_iban",
							"description": "Device user ID for fingerprint/biometric attendance",
						},
						{
							"fieldname": "linked_user",
							"label": "Linked User (ESS)",
							"fieldtype": "Link",
							"options": "User",
							"insert_after": "biometric_user_id",
							"description": "User account for employee self-service portal",
						},
					]
				)

			if employee_fields:
				custom_fields_map["Employee"] = employee_fields

		if frappe.db.exists("DocType", "HR Payroll Entry") and frappe.db.exists("DocType", "HR Salary Slip"):
			anchor = "owner_user"
			if not frappe.db.exists("Custom Field", {"dt": "HR Payroll Entry", "fieldname": "hr_payroll_branch"}):
				custom_fields_map.setdefault("HR Payroll Entry", []).extend(
					[
						{
							"fieldname": "hr_payroll_extend_section",
							"label": "Payroll linkage",
							"fieldtype": "Section Break",
							"insert_after": anchor,
						},
						{
							"fieldname": "hr_payroll_branch",
							"label": "Branch",
							"fieldtype": "Link",
							"options": "Branch",
							"insert_after": "hr_payroll_extend_section",
						},
						{
							"fieldname": "hr_payroll_cost_center",
							"label": "Cost Center",
							"fieldtype": "Link",
							"options": "Cost Center",
							"insert_after": "hr_payroll_branch",
						},
						{
							"fieldname": "payroll_currency",
							"label": "Currency",
							"fieldtype": "Link",
							"options": "Currency",
							"insert_after": "hr_payroll_cost_center",
						},
						{
							"fieldname": "hr_salary_slip",
							"label": "Salary Slip",
							"fieldtype": "Link",
							"options": "HR Salary Slip",
							"insert_after": "payroll_currency",
						},
					]
				)

		if custom_fields_map:
			create_custom_fields(custom_fields_map, update=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa HR: ensure_hr_custom_fields")
