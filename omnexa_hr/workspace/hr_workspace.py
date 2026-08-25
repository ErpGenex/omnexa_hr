# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""Full HR workspace — international HRMS catalog (ISO 30414 / SHRM aligned)."""

from __future__ import annotations

import json

import frappe

from omnexa_core.omnexa_core.vertical_workspace_sync import drop_missing_workspace_dashboard_links

WorkspaceLink = tuple[str, str, str]

WORKSPACE_NAME = "HR"

# Non-HR links that must never appear on the HR desk (ERP padding / legacy sync).
_FORBIDDEN_HR_LINKS = frozenset(
	{
		"Patient",
		"Customer",
		"Supplier",
		"Item",
		"Sales Invoice",
		"Purchase Invoice",
		"Payment Entry",
		"Journal Entry",
		"GL Account",
		"Cost Center",
		"Company",
		"Branch",
		"General Ledger",
		"Trial Balance",
		"Accounts Receivable",
		"Accounts Payable",
		"Sales Register",
		"Purchase Register",
		"Profit and Loss Statement",
		"Balance Sheet",
		"Governance Overview",
		"Sales Order",
		"Delivery Note",
		"Purchase Order",
	}
)

_FORBIDDEN_HR_SECTION_LABELS = frozenset(
	{
		"ERP masters",
		"ERP masters · 1",
		"ERP masters · 2",
		"ERP masters · 3",
		"ERP reports",
		"ERP reports · 1",
		"ERP reports · 2",
		"💳 ERP masters",
		"💳 ERP masters · 1",
		"💳 ERP masters · 2",
		"📈 ERP reports",
		"📈 ERP reports · 1",
		"📈 ERP reports · 2",
		"Finance",
		"💰 Finance",
	}
)

_SHORTCUT_COLORS = ("Blue", "Green", "Orange", "Red", "Cyan", "Purple", "Teal", "Pink", "Yellow")

WORKSPACE_SECTIONS: list[tuple[str, list[WorkspaceLink]]] = [
	(
		"📊 Dashboards",
		[
			("Page", "hr-executive-dashboard", "Executive Dashboard"),
			("Page", "hr-analytics-dashboard", "Analytics Dashboard"),
			("Page", "hr-employee-self-service", "Employee Self-Service"),
			("Page", "hr-operations-desk", "Operations Desk"),
		],
	),
	(
		"👥 Workforce",
		[
			("Page", "employee-directory", "Employee Directory"),
			("DocType", "Employee", "Employee"),
			("DocType", "HR Department", "Department"),
			("DocType", "HR Shift Type", "Shift Type"),
		],
	),
	(
		"🎯 Talent Acquisition",
		[
			("DocType", "HR Recruitment Request", "Recruitment Request"),
			("DocType", "HR Job Applicant", "Job Applicant"),
			("DocType", "HR Interview", "Interview"),
		],
	),
	(
		"⏱ Attendance & Biometric",
		[
			("DocType", "HR Attendance", "Attendance"),
			("DocType", "HR Biometric Device", "Biometric Device"),
			("DocType", "HR Biometric Punch Log", "Punch Log"),
		],
	),
	(
		"🏖 Leave",
		[
			("DocType", "HR Leave Type", "Leave Type"),
			("DocType", "HR Leave Balance", "Leave Balance"),
			("DocType", "HR Leave Application", "Leave Application"),
		],
	),
	(
		"📚 Learning & Performance",
		[
			("DocType", "HR Training Record", "Training Record"),
			("DocType", "HR Employee Appraisal", "Employee Appraisal"),
		],
	),
	(
		"💰 Payroll & Benefits",
		[
			("DocType", "HR Payroll Run", "Payroll Run"),
			("DocType", "HR Salary Slip", "Salary Slip"),
			("DocType", "HR Payroll Entry", "Payroll Entry"),
			("DocType", "HR Salary Advance", "Salary Advance"),
			("DocType", "HR End of Service Settlement", "End of Service"),
		],
	),
	(
		"📈 Reports",
		[
			("Report", "HR Headcount", "Headcount"),
			("Report", "HR Attendance Summary", "Attendance Summary"),
			("Report", "HR Leave Application Summary", "Leave Summary"),
			("Report", "HR Payroll Register", "Payroll Register"),
			("Report", "HR Recruitment Pipeline", "Recruitment Pipeline"),
			("Report", "HR Training Summary", "Training Summary"),
		],
	),
	(
		"⚙ Setup",
		[
			("DocType", "HR Settings", "HR Settings"),
			("DocType", "HR Payroll Company Settings", "Payroll Settings"),
		],
	),
]


def _link_exists(link_type: str, link_to: str) -> bool:
	if link_type == "DocType":
		return bool(frappe.db.exists("DocType", link_to))
	if link_type == "Report":
		return bool(frappe.db.exists("Report", link_to))
	if link_type == "Page":
		return bool(frappe.db.exists("Page", link_to))
	return False


def _build_link_rows() -> list[dict]:
	"""HR-only workspace links — no ERP finance padding from global catalog."""
	rows: list[dict] = []
	seen: set[tuple[str, str]] = set()
	for section_label, items in WORKSPACE_SECTIONS:
		valid = [(t, to, label) for t, to, label in items if _link_exists(t, to)]
		if not valid:
			continue
		rows.append({"label": section_label, "type": "Card Break", "link_type": "DocType"})
		for link_type, link_to, label in valid:
			key = (link_type, link_to)
			if key in seen:
				continue
			seen.add(key)
			row: dict = {
				"type": "Link",
				"label": label,
				"link_type": link_type,
				"link_to": link_to,
				"is_query_report": 1 if link_type == "Report" else 0,
			}
			if link_type == "Report":
				row["report_ref_doctype"] = frappe.db.get_value("Report", link_to, "ref_doctype")
			rows.append(row)
	return rows


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
				"color": _SHORTCUT_COLORS[idx % len(_SHORTCUT_COLORS)],
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
			"data": {"text": '<span class="h4"><b>HR</b></span>', "col": 12},
		}
	)
	section_idx = 0
	link_idx = 0
	for row in link_rows:
		if row.get("type") == "Card Break":
			if section_idx:
				content.append({"id": f"hr-sp-{section_idx}", "type": "spacer", "data": {"col": 12}})
			content.append(
				{
					"id": f"hr-sec-{section_idx}",
					"type": "header",
					"data": {"text": f'<span class="h5"><b>{row["label"]}</b></span>', "col": 12},
				}
			)
			section_idx += 1
			continue
		content.append(
			{
				"id": f"hr-lnk-{link_idx}",
				"type": "shortcut",
				"data": {"shortcut_name": row["label"], "col": 4},
			}
		)
		link_idx += 1

	if ws.number_cards:
		content.append({"id": "hr-kpi-sp", "type": "spacer", "data": {"col": 12}})
		content.append(
			{
				"id": "hr-kpi-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📊 KPIs</b></span>', "col": 12},
			}
		)
		for idx, nc in enumerate(ws.number_cards):
			content.append(
				{
					"id": f"hr-nc-{idx}",
					"type": "number_card",
					"data": {"number_card_name": nc.number_card_name, "col": 4},
				}
			)

	if ws.charts:
		content.append({"id": "hr-ch-sp", "type": "spacer", "data": {"col": 12}})
		content.append(
			{
				"id": "hr-ch-h",
				"type": "header",
				"data": {"text": '<span class="h5"><b>📈 Charts</b></span>', "col": 12},
			}
		)
		for idx, ch in enumerate(ws.charts):
			content.append(
				{
					"id": f"hr-ch-{idx}",
					"type": "chart",
					"data": {"chart_name": ch.label or ch.chart_name, "col": 4},
				}
			)

	return json.dumps(content, separators=(",", ":"))


def _allowed_hr_link_keys() -> set[tuple[str, str]]:
	allowed: set[tuple[str, str]] = set()
	for _section, items in WORKSPACE_SECTIONS:
		for link_type, link_to, _label in items:
			if _link_exists(link_type, link_to):
				allowed.add((link_type, link_to))
	return allowed


def purge_non_hr_workspace_artifacts(ws) -> dict:
	"""Remove ERP/finance padding accidentally merged into HR workspace."""
	removed_links = 0
	removed_shortcuts = 0
	allowed = _allowed_hr_link_keys()

	new_links = []
	for row in list(ws.links or []):
		if row.type == "Card Break":
			label = (row.label or "").strip()
			if any(token in label for token in _FORBIDDEN_HR_SECTION_LABELS):
				removed_links += 1
				continue
			new_links.append(row)
			continue
		key = (row.link_type, row.link_to)
		if row.link_to in _FORBIDDEN_HR_LINKS or key not in allowed:
			removed_links += 1
			continue
		new_links.append(row)
	ws.links = new_links

	new_shortcuts = []
	for row in list(ws.shortcuts or []):
		key = (row.type, row.link_to)
		if row.link_to in _FORBIDDEN_HR_LINKS or (row.type != "URL" and key not in allowed):
			removed_shortcuts += 1
			continue
		new_shortcuts.append(row)
	ws.shortcuts = new_shortcuts

	return {"removed_links": removed_links, "removed_shortcuts": removed_shortcuts}


def sync_hr_workspace_menu(*, save: bool = True, rebuild: bool = True) -> dict:
	stats = {"sections": 0, "links": 0, "shortcuts": 0}
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
	stats["purged"] = purge_non_hr_workspace_artifacts(ws)
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
		"links_catalogued": len(link_rows),
	}
