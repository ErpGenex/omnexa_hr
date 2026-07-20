# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Full HR workspace — global leader catalog."""

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.vertical_workspace_sync import (
	build_link_rows_for_app,
	drop_missing_workspace_dashboard_links,
)

WorkspaceLink = tuple[str, str, str]

WORKSPACE_NAME = "HR"

_SHORTCUT_COLORS = ("Blue", "Green", "Orange", "Red", "Cyan", "Purple", "Teal", "Pink", "Yellow")

WORKSPACE_SECTIONS: list[tuple[str, list[WorkspaceLink]]] = [('📊 Dashboards', [('Page', 'hr-executive-dashboard', 'Executive Dashboard'), ('Page', 'hr-employee-self-service', 'Employee Self-Service')]), ('👥 Workforce', [('DocType', 'Employee', 'Employee'), ('DocType', 'HR Leave Type', 'Leave Type'), ('DocType', 'HR Leave Application', 'Leave Application'), ('DocType', 'HR Attendance', 'Attendance')]), ('💰 Payroll', [('DocType', 'HR Payroll Run', 'Payroll Run'), ('DocType', 'HR Salary Slip', 'Salary Slip'), ('DocType', 'HR Payroll Entry', 'Payroll Entry')]), ('📈 Reports', [('Report', 'HR Headcount', 'Headcount'), ('Report', 'HR Payroll Register', 'Payroll Register'), ('Report', 'HR Attendance Summary', 'Attendance Summary')]), ('💰 Finance', [('DocType', 'Journal Entry', 'Journal Entry')])]



def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	return False


def _build_link_rows() -> list[dict]:
	return build_link_rows_for_app("omnexa_hr", WORKSPACE_SECTIONS)


def _build_shortcuts(link_rows: list[dict]) -> list[dict]:
	shortcuts: list[dict] = []
	idx = 0
	priority_types = ("Page", "DocType", "Report", "Dashboard")
	links = [r for r in link_rows if r.get("type") == "Link"]
	for lt in priority_types:
		for row in links:
			if row.get("link_type") != lt:
				continue
			entry = {
				"label": row["label"],
				"link_to": row["link_to"],
				"type": row["link_type"],
				"color": _SHORTCUT_COLORS[idx % len(_SHORTCUT_COLORS)]
	}
			if lt == "DocType":
				entry["doc_view"] = "List"
			if lt == "Report" and row.get("report_ref_doctype"):
				entry["report_ref_doctype"] = row["report_ref_doctype"]
			shortcuts.append(entry)
			idx += 1
	return shortcuts


def _onboarding_blocks(existing_content: str | None) -> list[dict]:
	if not existing_content:
		return []
	try:
		blocks = json.loads(existing_content)
	except json.JSONDecodeError:
		return []
	return [b for b in blocks if b.get("type") == "onboarding"]


def _build_content(link_rows: list[dict], ws) -> str:
	content: list[dict] = []
	content.extend(_onboarding_blocks(ws.content))
	content.append(
		{
			"id": "hr-title",
			"type": "header",
			"data": {"text": '<span class="h4"><b>HR</b></span>', "col": 12}
	}
	)
	section_idx = 0
	link_idx = 0
	for row in link_rows:
		if row.get("type") == "Card Break":
			if section_idx:
				content.append({"id": f"hr-sp-{section_idx
	}", "type": "spacer", "data": {"col": 12}
	})
			content.append(
				{
					"id": f"hr-sec-{section_idx
	}",
					"type": "header",
					"data": {"text": f'<span class="h5"><b>{row["label"]
	}</b></span>', "col": 12}
	}
			)
			section_idx += 1
			continue
		content.append(
			{
				"id": f"hr-lnk-{link_idx
	}",
				"type": "shortcut",
				"data": {"shortcut_name": row["label"], "col": 4}
	}
		)
		link_idx += 1

	if ws.number_cards:
		content.append({"id": "hr-kpi-sp", "type": "spacer", "data": {"col": 12}
	})
		content.append(
			{
				"id": "hr-kpi-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📊 KPIs</b></span>', "col": 12}
	}
		)
		for idx, nc in enumerate(ws.number_cards):
			content.append(
				{
					"id": f"hr-nc-{idx
	}",
					"type": "number_card",
					"data": {"number_card_name": nc.number_card_name, "col": 4}
	}
			)

	if ws.charts:
		content.append({"id": "hr-ch-sp", "type": "spacer", "data": {"col": 12}
	})
		content.append(
			{
				"id": "hr-ch-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📈 Charts</b></span>', "col": 12}
	}
		)
		for idx, ch in enumerate(ws.charts):
			content.append(
				{
					"id": f"hr-ch-{idx
	}",
					"type": "chart",
					"data": {"chart_name": ch.label or ch.chart_name, "col": 4}
	}
			)

	return json.dumps(content, separators=(",", ":"))


def sync_hr_workspace_menu(*, save: bool = True, rebuild: bool = True) -> dict:
	stats = {"sections": 0, "links": 0, "shortcuts": 0
	}
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return stats
	rows = _build_link_rows()
	link_rows = [r for r in rows if r.get("type") == "Link"]
	new_shortcuts = _build_shortcuts(rows)
	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	if rebuild:
		ws.set("links", [])
		ws.set("shortcuts", [])
	for row in rows:
		if row["type"] == "Card Break":
			stats["sections"] += 1
		else:
			stats["links"] += 1
		ws.append("links", row)
	for sc in new_shortcuts:
		ws.append("shortcuts", sc)
	stats["shortcuts"] = len(new_shortcuts)
	drop_missing_workspace_dashboard_links(ws)
	ws.content = _build_content(rows, ws)
	stats["content_blocks"] = len(json.loads(ws.content))
	if save:
		ws.flags.ignore_permissions = True
		ws.flags.ignore_version = True
		latest = frappe.db.get_value("Workspace", WORKSPACE_NAME, "modified")
		if latest:
			ws._original_modified = latest
		ws.save()
		frappe.clear_cache(doctype="Workspace")
	stats["total_links"] = len(link_rows)
	return stats


@frappe.whitelist()
def get_workspace_coverage() -> dict:
	rows = _build_link_rows()
	link_rows = [r for r in rows if r.get("type") == "Link"]
	return {
		"sections": len([r for r in rows if r.get("type") == "Card Break"]),
		"links_catalogued": len(link_rows)
	}
