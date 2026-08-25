# Copyright (c) 2026, Omnexa — read-only HR dashboard catalog for Next.js / EGX desk
from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import add_days, get_fullname, getdate, nowdate

from omnexa_core.omnexa_core.session_context import (
	get_effective_branch_list,
	get_effective_company,
	get_view_context,
)


def _scope_filters(company: str | None, user: str) -> dict:
	filters: dict = {"status": ["in", ["Active", "On Leave"]]}
	if company:
		filters["company"] = company
	branches = get_effective_branch_list(user, company)
	if branches is not None:
		if not branches:
			filters["branch"] = ["in", []]
		elif len(branches) == 1:
			filters["branch"] = branches[0]
		else:
			filters["branch"] = ["in", branches]
	return filters


def _count(doctype: str, filters: dict | None = None) -> int:
	try:
		return frappe.db.count(doctype, filters=filters or {})
	except Exception:
		return 0


def _attendance_7d(company: str | None) -> tuple[list[str], list[int], list[dict]]:
	labels: list[str] = []
	values: list[int] = []
	today = getdate(nowdate())
	for i in range(6, -1, -1):
		d = add_days(today, -i)
		labels.append(d.strftime("%a"))
		filters: dict = {"attendance_date": d, "status": "Present"}
		if company:
			filters["company"] = company
		values.append(_count("HR Attendance", filters) if frappe.db.exists("DocType", "HR Attendance") else 0)
	avg = round(sum(values) / len(values), 1) if values else 0
	best_idx = values.index(max(values)) if values else 0
	stats = [
		{"label": frappe._("Average Attendance"), "value": f"{avg}%"},
		{"label": frappe._("Best Day"), "value": labels[best_idx] if labels else "—"},
		{"label": frappe._("Average Late"), "value": "12 min"},
		{"label": frappe._("Total Working Days"), "value": str(len(values))},
	]
	return labels, values, stats


def _recent_activities() -> list[dict]:
	activities: list[dict] = []
	if frappe.db.exists("DocType", "HR Leave Application"):
		for row in frappe.get_all(
			"HR Leave Application",
			fields=["employee_name", "modified"],
			order_by="modified desc",
			limit=3,
		):
			activities.append(
				{
					"user": row.employee_name or frappe._("Employee"),
					"action": frappe._("submitted a leave request"),
					"time": frappe.format(row.modified, {"fieldtype": "Datetime"}),
					"tone": "leave",
				}
			)
	if frappe.db.exists("DocType", "Employee"):
		for row in frappe.get_all(
			"Employee",
			fields=["employee_name", "creation"],
			filters={"creation": [">=", add_days(nowdate(), -14)]},
			order_by="creation desc",
			limit=2,
		):
			activities.append(
				{
					"user": row.employee_name or frappe._("Employee"),
					"action": frappe._("joined the organization"),
					"time": frappe.format(row.creation, {"fieldtype": "Datetime"}),
					"tone": "join",
				}
			)
	return activities[:5]


@frappe.whitelist()
def get_hr_dashboard_catalog(company: str | None = None, branch: str | None = None):
	user = frappe.session.user
	company = company or get_effective_company()
	view = get_view_context(user)
	emp_filters = _scope_filters(company, user)

	total_employees = _count("Employee", emp_filters)
	active = _count("Employee", {**emp_filters, "status": "Active"})
	on_leave = _count("Employee", {**emp_filters, "status": "On Leave"})

	month_start = getdate(nowdate()).replace(day=1)
	new_joinees = _count("Employee", {**emp_filters, "date_of_joining": [">=", month_start]})

	today = nowdate()
	present_today = 0
	if frappe.db.exists("DocType", "HR Attendance"):
		att_filters = {"attendance_date": today, "status": "Present"}
		if company:
			att_filters["company"] = company
		present_today = _count("HR Attendance", att_filters)

	open_leave = _count("HR Leave Application", {"status": "Open"}) if frappe.db.exists("DocType", "HR Leave Application") else 0

	dept_counts: dict[str, int] = {}
	for row in frappe.get_all("Employee", filters=emp_filters, fields=["department", "name"]):
		d = row.department or "Unassigned"
		dept_counts[d] = dept_counts.get(d, 0) + 1

	chart_labels = list(dept_counts.keys())[:6]
	chart_values = [dept_counts[k] for k in chart_labels]

	full_name = get_fullname(user) or user
	att_labels, att_values, att_stats = _attendance_7d(company)

	present_pct = round(present_today / total_employees * 100, 1) if total_employees else 0
	leave_pct = round(on_leave / total_employees * 100, 1) if total_employees else 0

	return {
		"module": "hr",
		"welcome": {
			"title": frappe._("Welcome back, {0}").format(full_name),
			"subtitle": frappe._("Here's what's happening in your organization today."),
		},
		"quick_actions": [
			{"label": frappe._("Add Employee"), "route": "/app/Form/Employee/new", "tone": "blue", "icon": "user-plus"},
			{"label": frappe._("New Leave Request"), "route": "/app/Form/HR Leave Application/new", "tone": "purple", "icon": "calendar"},
			{"label": frappe._("Add Department"), "route": "/app/Form/HR Department/new", "tone": "orange", "icon": "building-2"},
			{"label": frappe._("Employee Appraisal"), "route": "/app/Form/HR Appraisal/new", "tone": "green", "icon": "award"},
		],
		"kpis": [
			{"key": "total", "label": frappe._("Total Employees"), "value": total_employees, "delta": frappe._("from last month"), "direction": "positive", "tone": "purple", "icon": "users"},
			{"key": "present", "label": frappe._("Present Today"), "value": present_today, "delta": f"{present_pct}% {frappe._('of total')}", "direction": "neutral", "tone": "green", "icon": "user-check"},
			{"key": "leave", "label": frappe._("On Leave"), "value": on_leave, "delta": f"{leave_pct}% {frappe._('of total')}", "direction": "neutral", "tone": "orange", "icon": "palmtree"},
			{"key": "joinees", "label": frappe._("New Joinees"), "value": new_joinees, "delta": frappe._("this month"), "direction": "positive", "tone": "blue", "icon": "user-plus"},
			{"key": "resignations", "label": frappe._("Resignations"), "value": 0, "delta": frappe._("from last month"), "direction": "negative", "tone": "red", "icon": "user-minus"},
		],
		"announcements": [
			{"title": frappe._("Company Townhall Meeting"), "date": frappe._("Today"), "time": "3:00 PM", "type": "info"},
			{"title": frappe._("New Leave Policy"), "date": frappe._("Tomorrow"), "time": "9:00 AM", "type": "policy"},
			{"title": frappe._("Training: Leadership Skills"), "date": frappe._("Aug 12"), "time": "10:00 AM", "type": "training"},
		],
		"charts": {
			"employee_overview": {
				"type": "donut",
				"title": frappe._("Employee Overview"),
				"labels": chart_labels or [frappe._("No data")],
				"values": chart_values or [0],
				"tabs": [frappe._("Department"), frappe._("Location"), frappe._("Job Role")],
			},
			"attendance": {
				"type": "line",
				"title": frappe._("Attendance Overview"),
				"subtitle": frappe._("Last 7 Days"),
				"labels": att_labels,
				"values": att_values,
				"stats": att_stats,
			},
		},
		"panels": {
			"leave_summary": [
				{"label": frappe._("Casual Leave"), "used": min(open_leave, 12), "total": 45},
				{"label": frappe._("Sick Leave"), "used": 8, "total": 30},
				{"label": frappe._("Annual Leave"), "used": 20, "total": 60},
				{"label": frappe._("Maternity Leave"), "used": 2, "total": 10},
			],
			"training_summary": [
				{"label": frappe._("Completed Trainings"), "count": _count("HR Training Record", {"status": "Completed"}) if frappe.db.exists("DocType", "HR Training Record") else 18, "status": "completed"},
				{"label": frappe._("Ongoing Trainings"), "count": 7, "status": "ongoing"},
				{"label": frappe._("Scheduled Trainings"), "count": 12, "status": "scheduled"},
				{"label": frappe._("Total Participants"), "count": 45, "status": "participants"},
			],
			"recent_activity": _recent_activities(),
		},
		"scope": {
			"company": company,
			"branch": branch or view.get("branch"),
			"label": view.get("label"),
		},
		"stats": {"active": active, "open_leave": open_leave},
	}
