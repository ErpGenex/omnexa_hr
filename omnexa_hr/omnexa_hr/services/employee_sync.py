# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe.utils import cint

from omnexa_core.omnexa_core.branch_access import get_default_branch


def sync_employees_from_practitioners(company: str, dry_run: bool = False) -> dict:
	"""Create Employee records from Healthcare Practitioners for HR directory / payroll."""
	if not frappe.db.exists("DocType", "Healthcare Practitioner"):
		return {"created": 0, "updated": 0, "skipped": 0, "reason": "Healthcare not installed"}

	practitioners = frappe.get_all(
		"Healthcare Practitioner",
		filters={"company": company, "status": "Active"},
		fields=["name", "practitioner_name", "license_number", "user", "website_photo"],
		limit=5000,
	)

	created = updated = skipped = 0
	for row in practitioners:
		branch = _primary_practitioner_branch(row.name) or get_default_branch(company)
		if not branch:
			skipped += 1
			continue

		employee_code = (row.license_number or row.name).strip()
		existing = frappe.db.get_value(
			"Employee",
			{"external_reference": row.name},
			"name",
		) or frappe.db.get_value("Employee", {"employee_code": employee_code, "company": company}, "name")

		if existing:
			if not dry_run:
				_updates = {"status": "Active", "branch": branch}
				if row.website_photo:
					_updates["employee_photo"] = row.website_photo
				if row.user and frappe.db.has_column("Employee", "linked_user"):
					_updates["linked_user"] = row.user
				frappe.db.set_value("Employee", existing, _updates, update_modified=False)
			updated += 1
			continue

		if dry_run:
			created += 1
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Employee",
				"employee_code": employee_code,
				"employee_name": row.practitioner_name,
				"company": company,
				"branch": branch,
				"designation": "Healthcare Practitioner",
				"status": "Active",
				"employment_type": "Full-time",
				"employee_photo": row.website_photo,
				"external_reference": row.name,
			}
		)
		if row.user and frappe.db.has_column("Employee", "linked_user"):
			doc.linked_user = row.user
		doc.flags.ignore_branch_access = True
		doc.insert(ignore_permissions=True)
		created += 1

	if not dry_run and (created or updated):
		frappe.db.commit()

	return {"created": created, "updated": updated, "skipped": skipped, "company": company}


def _primary_practitioner_branch(practitioner: str) -> str | None:
	assignments = frappe.get_all(
		"Healthcare Practitioner Branch",
		filters={"parent": practitioner, "is_active": 1},
		fields=["branch"],
		order_by="idx asc",
		limit=1,
	)
	if assignments:
		return assignments[0].branch
	assignments = frappe.get_all(
		"Healthcare Practitioner Branch",
		filters={"parent": practitioner},
		fields=["branch"],
		order_by="idx asc",
		limit=1,
	)
	return assignments[0].branch if assignments else None


@frappe.whitelist()
def sync_company_employees(company: str | None = None, dry_run: int | str = 0) -> dict:
	frappe.only_for(("System Manager", "HR Manager", "Company Admin"))
	from omnexa_core.omnexa_core.session_context import get_effective_company

	company = company or get_effective_company()
	if not company:
		frappe.throw(frappe._("Select a company first."))
	return sync_employees_from_practitioners(company, dry_run=cint(dry_run))
