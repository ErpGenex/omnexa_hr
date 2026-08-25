# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.activity_labels import get_company_activity_info


def has_app_permission() -> bool:
	"""Show HR app when company activity includes HR or user has HR role."""
	if frappe.session.user == "Guest":
		return False
	roles = set(frappe.get_roles())
	if roles & {"System Manager", "HR Manager", "HR User", "HR Employee", "Company Admin"}:
		return True
	from omnexa_core.omnexa_core.session_context import get_effective_company

	company = get_effective_company()
	if not company:
		return True
	info = get_company_activity_info(company)
	activity = (info.get("activity") or "").lower()
	return "hr" in activity or activity in ("", "general")
