# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


SUPPORTED_FRAPPE_MAJOR = 15


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


def ensure_hr_custom_fields():
	"""Non-destructive HR enterprise fields on Employee and legacy payroll row."""
	try:
		custom_fields_map: dict = {}

		if frappe.db.exists("DocType", "Employee"):
			if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": "employee_name_ar"
	}):
				custom_fields_map.setdefault("Employee", []).extend(
					[
						{
							"fieldname": "hr_identity_section",
							"label": "HR Identity",
							"fieldtype": "Section Break",
							"insert_after": "employee_name"
	},
						{
							"fieldname": "employee_name_ar",
							"label": "Employee Name (Arabic)",
							"fieldtype": "Data",
							"insert_after": "hr_identity_section"
	},
						{
							"fieldname": "national_id",
							"label": "National ID",
							"fieldtype": "Data",
							"insert_after": "employee_name_ar"
	},
						{
							"fieldname": "passport_number",
							"label": "Passport Number",
							"fieldtype": "Data",
							"insert_after": "national_id"
	},
						{
							"fieldname": "employment_type",
							"label": "Employment Type",
							"fieldtype": "Select",
							"options": "Full-time\nPart-time\nContract\nFreelancer",
							"insert_after": "passport_number"
	},
						{
							"fieldname": "hr_default_cost_center",
							"label": "Default Cost Center (payroll)",
							"fieldtype": "Link",
							"options": "Cost Center",
							"insert_after": "department"
	},
						{
							"fieldname": "salary_bank_account_no",
							"label": "Salary Bank Account No.",
							"fieldtype": "Data",
							"insert_after": "external_reference"
	},
						{
							"fieldname": "salary_iban",
							"label": "Salary IBAN",
							"fieldtype": "Data",
							"insert_after": "salary_bank_account_no"
	},
					]
				)

		if frappe.db.exists("DocType", "HR Payroll Entry") and frappe.db.exists("DocType", "HR Salary Slip"):
			anchor = "owner_user"
			if not frappe.db.exists("Custom Field", {"dt": "HR Payroll Entry", "fieldname": "hr_payroll_branch"
	}):
				custom_fields_map.setdefault("HR Payroll Entry", []).extend(
					[
						{
							"fieldname": "hr_payroll_extend_section",
							"label": "Payroll linkage",
							"fieldtype": "Section Break",
							"insert_after": anchor
	},
						{
							"fieldname": "hr_payroll_branch",
							"label": "Branch",
							"fieldtype": "Link",
							"options": "Branch",
							"insert_after": "hr_payroll_extend_section"
	},
						{
							"fieldname": "hr_payroll_cost_center",
							"label": "Cost Center",
							"fieldtype": "Link",
							"options": "Cost Center",
							"insert_after": "hr_payroll_branch"
	},
						{
							"fieldname": "payroll_currency",
							"label": "Currency",
							"fieldtype": "Link",
							"options": "Currency",
							"insert_after": "hr_payroll_cost_center"
	},
						{
							"fieldname": "hr_salary_slip",
							"label": "Salary Slip",
							"fieldtype": "Link",
							"options": "HR Salary Slip",
							"insert_after": "payroll_currency"
	},
					]
				)

		if custom_fields_map:
			create_custom_fields(custom_fields_map, update=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Omnexa HR: ensure_hr_custom_fields")
