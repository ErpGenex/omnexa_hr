# i18n:managed-catalog — bilingual/regional catalog; UI via ar.csv
# Copyright (c) 2026, Omnexa
"""Role-scoped desk context for HR portal pages — Trading-style layout."""

from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.app_logo_registry import get_logo_url
from omnexa_core.vertical_workcenter.default_portal_catalog import get_grouped_portal_catalog_for_app
from omnexa_core.vertical_workcenter.portal_role_policy import is_portal_admin
from omnexa_core.vertical_workcenter.portal_menu_item import build_portal_menu_item
from omnexa_core.vertical_workcenter.registry import get_registry_entry
from omnexa_hr.workspace.hr_workspace import WORKSPACE_SECTIONS, _link_exists

ROLE_MENU_SECTIONS: dict[str, list[str] | None] = {
	"workcenter": None,
	"executive-dashboard": ["📊 Dashboards", "👥 Workforce", "📈 Reports"],
	"operations-desk": ["⏱ Attendance & Biometric", "🏖 Leave", "👥 Workforce", "🎯 Talent Acquisition"],
	"finance-desk": ["💰 Payroll & Benefits", "📈 Reports"],
	"customer-portal": ["📊 Dashboards", "👥 Workforce"],
	"analytics-dashboard": ["📊 Dashboards", "📈 Reports", "👥 Workforce"],
}


def _route_for_link(link_type: str, link_to: str) -> str:
	if link_type == "Page":
		return f"/app/{link_to}"
	if link_type == "DocType":
		return f"/app/List/{link_to.replace(' ', '%20')}"
	if link_type == "Report":
		return f"/app/query-report/{link_to.replace(' ', '%20')}"
	if link_type == "Workspace":
		return f"/app/{link_to}"
	return f"/app/{link_to}"


def _build_menu_sections(role_key: str, *, is_admin: bool) -> list[dict]:
	allowed_titles = ROLE_MENU_SECTIONS.get(role_key)
	out: list[dict] = []
	for section_title, links in WORKSPACE_SECTIONS:
		if allowed_titles is not None and section_title not in allowed_titles:
			if not is_admin:
				continue
		items: list[dict] = []
		for link in links or []:
			if not link or len(link) < 2:
				continue
			link_type, link_to = link[0], link[1]
			label = link[2] if len(link) > 2 else link_to
			if not _link_exists(link_type, link_to):
				continue
			items.append(
				build_portal_menu_item("omnexa_hr", link_type, link_to, label, _route_for_link(link_type, link_to))
			)
		if items:
			out.append({"title_en": section_title, "title_ar": section_title, "items": items})
	return out


def _find_portal(groups: list[dict], role_key: str) -> dict | None:
	page_id = f"hr-{role_key}"
	for group in groups or []:
		for portal in group.get("portals") or []:
			pid = portal.get("id") or ""
			if pid == page_id or pid.endswith(role_key) or portal.get("page") == page_id:
				return portal
	return None


def _hr_dashboard_payload() -> dict:
	from omnexa_hr.omnexa_hr.api.hr_dashboard import get_hr_dashboard_catalog

	try:
		return get_hr_dashboard_catalog() or {}
	except Exception:
		return {}


def _role_kpis(role_key: str, catalog: dict) -> list[dict]:
	raw = catalog.get("kpis") or []
	if raw:
		return [
			{
				"title_en": k.get("label") or k.get("label_en") or k.get("key"),
				"title_ar": k.get("label_ar") or k.get("label") or k.get("key"),
				"value": k.get("value", 0),
				"icon": {"users": "👥", "user-check": "✅", "palmtree": "🏖️", "user-plus": "➕", "user-minus": "➖"}.get(
					k.get("icon"), "📊"
				),
			}
			for k in raw[:5]
		]
	stats = catalog.get("stats") or {}
	return [
		{"title_en": "Active Employees", "title_ar": "موظفون نشطون", "value": stats.get("active", 0), "icon": "👥"},
		{"title_en": "Open Leave", "title_ar": "إجازات مفتوحة", "value": stats.get("open_leave", 0), "icon": "🏖️"},
	]


def _role_quick_actions(catalog: dict) -> list[dict]:
	icon_map = {
		"user-plus": "👤",
		"calendar": "📅",
		"building-2": "🏢",
		"award": "🏆",
	}
	return [
		{
			"label_en": a.get("label"),
			"label_ar": a.get("label"),
			"route": a.get("route"),
			"icon": icon_map.get(a.get("icon"), "⚡"),
		}
		for a in (catalog.get("quick_actions") or [])[:8]
	]


def _my_work(limit: int = 6) -> dict:
	work: dict = {"tasks": [], "hearings": [], "intake": []}
	if frappe.db.exists("DocType", "HR Leave Application"):
		work["intake"] = frappe.get_all(
			"HR Leave Application",
			filters={"status": "Open"},
			fields=["name", "employee_name", "status", "from_date"],
			order_by="modified desc",
			limit=limit,
		)
	if frappe.db.exists("DocType", "HR Job Applicant"):
		work["tasks"] = frappe.get_all(
			"HR Job Applicant",
			filters={"status": ["in", ["Open", "Replied"]]},
			fields=["name", "applicant_name", "status"],
			order_by="modified desc",
			limit=limit,
		)
	if frappe.db.exists("DocType", "HR Recruitment Request"):
		work["hearings"] = frappe.get_all(
			"HR Recruitment Request",
			filters={"status": ["in", ["Open", "Pending"]]},
			fields=["name", "designation", "status"],
			order_by="modified desc",
			limit=limit,
		)
	return work


def _role_dashboard(role_key: str, catalog: dict, work: dict) -> dict:
	return {
		"kpis": _role_kpis(role_key, catalog),
		"quick_actions": _role_quick_actions(catalog),
		"work_queue": work.get("hearings") or [],
		"pending_tasks": work.get("tasks") or [],
		"approvals": work.get("intake") or [],
		"charts": [
			{"title_en": "Attendance Trend", "title_ar": "اتجاه الحضور", "type": "line"},
			{"title_en": "Headcount", "title_ar": "عدد الموظفين", "type": "bar"},
		],
	}


def _portal_context(role_key: str) -> dict:
	groups = get_grouped_portal_catalog_for_app("omnexa_hr")
	portal = _find_portal(groups, role_key)
	entry = get_registry_entry("omnexa_hr") or {}
	is_admin = is_portal_admin() or frappe.session.user == "Administrator"
	menu_sections = _build_menu_sections(role_key, is_admin=is_admin)
	quick_links: list[dict] = []
	for section in menu_sections:
		quick_links.extend(section.get("items") or [])

	catalog = _hr_dashboard_payload()
	work = _my_work()
	dashboard = _role_dashboard(role_key, catalog, work)

	sibling_portals: list[dict] = []
	for group in groups:
		for p in group.get("portals") or []:
			if p.get("allowed") is not False:
				sibling_portals.append(p)

	return {
		"app": "omnexa_hr",
		"role_key": role_key,
		"is_admin": is_admin,
		"portal": portal,
		"title_en": (portal or {}).get("label_en") or entry.get("title_en", "Human Resources"),
		"title_ar": (portal or {}).get("label_ar") or entry.get("title_ar", "الموارد البشرية"),
		"role_en": (portal or {}).get("role_en") or role_key,
		"role_ar": (portal or {}).get("role_ar") or role_key,
		"icon": (portal or {}).get("icon") or "👥",
		"logo_url": get_logo_url("omnexa_hr"),
		"brand_name_en": "Omnexa HR",
		"brand_name_ar": "Omnexa HR — الموارد البشرية",
		"workcenter_route": "/app/hr-workcenter",
		"grouped_portals": groups,
		"sibling_portals": sibling_portals,
		"menu_sections": menu_sections,
		"quick_links": quick_links[:24],
		"dashboard": dashboard,
		"kpis": dashboard["kpis"],
	}


@frappe.whitelist()
def get_role_portal_context(role_key: str) -> dict:
	role_key = (role_key or "").strip()
	return _portal_context(role_key)


@frappe.whitelist()
def get_workcenter_context_api() -> dict:
	ctx = _portal_context("workcenter")
	ctx["title_en"] = "Human Resources Workcenter"
	ctx["title_ar"] = "مركز عمل الموارد البشرية"
	ctx["role_label_en"] = "HR Administrator"
	ctx["role_label_ar"] = "مسؤول الموارد البشرية"
	return ctx
