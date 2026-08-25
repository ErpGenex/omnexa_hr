# Copyright (c) 2026, Omnexa — HR workspace catalog for Next.js desk
from __future__ import annotations

import frappe

from omnexa_hr.workspace.hr_workspace import WORKSPACE_SECTIONS, _link_exists

# Frappe Page name → Next.js route (Phase 1 complete)
_NEXT_PAGE_ROUTES: dict[str, str] = {
	"hr-dashboard": "/hr/dashboard",
	"hr-executive-dashboard": "/hr/dashboard",
	"hr-analytics-dashboard": "/hr/analytics",
	"hr-employee-self-service": "/hr/self-service",
	"hr-operations-desk": "/hr/operations",
	"hr-workcenter": "/hr/workcenter",
	"hr-finance-desk": "/hr/finance",
	"hr-customer-portal": "/hr/customer-portal",
	"employee-directory": "/hr/employee-directory",
}


def _resolve_href(link_type: str, link_to: str) -> dict:
	"""Return Frappe-canonical href + optional Next.js route for unified desk."""
	if link_type == "Page":
		frappe_href = f"/app/{link_to}"
		next_href = _NEXT_PAGE_ROUTES.get(link_to)
		return {
			"href": frappe_href,
			"next_href": next_href or frappe_href,
			"external": next_href is None,
			"next_js": bool(next_href),
		}
	if link_type == "DocType":
		href = f"/app/List/{frappe.utils.quote(link_to)}"
		return {"href": href, "next_href": href, "external": True, "next_js": False}
	if link_type == "Report":
		href = f"/app/query-report/{frappe.utils.quote(link_to)}"
		return {"href": href, "next_href": href, "external": True, "next_js": False}
	href = f"/app/{link_to}"
	return {"href": href, "next_href": href, "external": True, "next_js": False}


@frappe.whitelist()
def get_hr_workspace_catalog():
	sections = []
	for section_label, items in WORKSPACE_SECTIONS:
		links = []
		for link_type, link_to, label in items:
			if not _link_exists(link_type, link_to):
				continue
			resolved = _resolve_href(link_type, link_to)
			links.append(
				{
					"label": label,
					"link_type": link_type,
					"link_to": link_to,
					**resolved,
				}
			)
		if links:
			sections.append({"title": section_label, "links": links})

	kpis = []
	if frappe.db.exists("DocType", "Employee"):
		from omnexa_hr.omnexa_hr.api.hr_dashboard import get_hr_dashboard_catalog

		try:
			catalog = get_hr_dashboard_catalog()
			kpis = catalog.get("kpis") or []
		except Exception:
			pass

	return {
		"module": "hr",
		"title": "HR",
		"sections": sections,
		"kpis": kpis[:4],
		"next_routes": list(_NEXT_PAGE_ROUTES.values()),
	}
