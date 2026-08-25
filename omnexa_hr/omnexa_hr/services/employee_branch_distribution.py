# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe


@frappe.whitelist()
def distribute_employees_to_branches(company: str, dry_run: int | str = 0) -> dict:
	"""Spread employees evenly across all branches of a company (education demo helper)."""
	frappe.only_for("System Manager")
	dry_run = int(dry_run or 0)

	branches = frappe.get_all(
		"Branch",
		filters={"company": company},
		pluck="name",
		order_by="is_head_office desc, branch_name asc",
	)
	if not branches:
		return {"updated": 0, "reason": "no branches"}

	employees = frappe.get_all(
		"Employee",
		filters={"company": company, "status": ["in", ["Active", "On Leave"]]},
		pluck="name",
		order_by="employee_name asc",
		limit=5000,
	)
	if not employees:
		return {"updated": 0, "reason": "no employees", "branches": branches}

	updated = 0
	for idx, emp in enumerate(employees):
		branch = branches[idx % len(branches)]
		current = frappe.db.get_value("Employee", emp, "branch")
		if current == branch:
			continue
		if dry_run:
			updated += 1
			continue
		frappe.db.set_value("Employee", emp, "branch", branch, update_modified=False)
		updated += 1

	if not dry_run and updated:
		frappe.db.commit()

	return {
		"company": company,
		"branches": branches,
		"employees": len(employees),
		"updated": updated,
		"dry_run": bool(dry_run),
	}
