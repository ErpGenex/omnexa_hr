# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe.utils import cint

from omnexa_core.omnexa_core.session_context import (
	get_effective_branch_list,
	get_effective_company,
	get_view_context,
)


def _branch_filters(company: str | None, branch: str | None, user: str) -> tuple[dict, list[str] | None]:
	"""Return branch filter fragment and the resolved branch scope."""
	scope: list[str] | None = None
	if branch:
		return {"branch": branch}, [branch]

	branches = get_effective_branch_list(user, company)
	if branches is None:
		return {}, None

	if not branches:
		return {"branch": ["in", []]}, []

	scope = list(branches)
	if len(scope) == 1:
		return {"branch": scope[0]}, scope
	return {"branch": ["in", scope]}, scope


@frappe.whitelist()
def get_employees(search: str | None = None, company: str | None = None, branch: str | None = None, limit: int = 60, start: int = 0):
	user = frappe.session.user
	company = company or get_effective_company()
	view = get_view_context(user)
	branch_filter, branch_scope = _branch_filters(company, branch, user)

	filters: dict = {"status": ["in", ["Active", "On Leave"]]}
	if company:
		filters["company"] = company
	if branch_filter:
		filters.update(branch_filter)
	if branch_scope == []:
		return {
			"employees": [],
			"total": 0,
			"company": company,
			"branch": branch,
			"branch_scope": branch_scope or [],
			"view_label": view.get("label"),
			"empty_reason": frappe._("No branch access for the current view scope."),
		}

	or_filters = None
	if search:
		term = f"%{search.strip()}%"
		or_filters = [
			["employee_name", "like", term],
			["employee_code", "like", term],
			["department", "like", term],
			["designation", "like", term],
		]

	fields = [
		"name",
		"employee_name",
		"employee_code",
		"employee_photo",
		"department",
		"designation",
		"company",
		"branch",
		"status",
		"employment_type",
		"date_of_joining",
	]

	employees = frappe.get_all(
		"Employee",
		filters=filters,
		or_filters=or_filters,
		fields=fields,
		order_by="employee_name asc",
		limit_page_length=cint(limit) or 60,
		limit_start=cint(start) or 0,
	)

	total = frappe.db.count("Employee", filters=filters)
	payload = {
		"employees": employees,
		"total": total,
		"company": company,
		"branch": branch,
		"branch_scope": branch_scope or [],
		"view_label": view.get("label"),
	}
	if not employees and company:
		company_filters = {"company": company, "status": ["in", ["Active", "On Leave"]]}
		company_total = frappe.db.count("Employee", company_filters)
		if company_total:
			payload["company_total"] = company_total
			payload["empty_reason"] = frappe._(
				"No employees in {0}. {1} employee(s) exist in other branches of {2} — switch to «All branches» in the top bar."
			).format(
				view.get("label") or branch or company,
				company_total,
				company,
			)
			payload["suggest_view_all"] = True
	elif not employees:
		payload["empty_reason"] = frappe._(
			"No active employees match {0}. Create Employee records or sync from Healthcare Practitioners."
		).format(view.get("label") or company or frappe._("the current scope"))
	return payload
