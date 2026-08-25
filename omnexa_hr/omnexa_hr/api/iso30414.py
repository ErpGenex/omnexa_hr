# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""ISO 30414 Human Capital Reporting metrics."""

from __future__ import annotations

import frappe
from frappe.utils import flt, getdate, today

from omnexa_core.omnexa_core.session_context import get_effective_branch_list, get_effective_company


ISO30414_AREAS = (
	("compliance_ethics", "Compliance & Ethics"),
	("costs", "Costs"),
	("diversity", "Diversity"),
	("leadership", "Leadership"),
	("culture", "Organizational Culture"),
	("health_safety", "Health, Safety & Well-being"),
	("productivity", "Productivity"),
	("recruitment_mobility", "Recruitment, Mobility & Turnover"),
	("skills", "Skills & Capabilities"),
	("succession", "Succession Planning"),
	("workforce_availability", "Workforce Availability"),
)


def _scoped_filters(company: str | None, branches: list[str] | None) -> tuple[dict, dict | None]:
	emp_filters: dict = {"status": "Active"}
	if company:
		emp_filters["company"] = company
	if branches is not None:
		if not branches:
			return emp_filters, {"employee": ["in", []]}
		emp_filters["branch"] = ["in", branches]
	return emp_filters, None


@frappe.whitelist()
def get_iso30414_metrics(company: str | None = None, branch: str | None = None) -> dict:
	company = company or get_effective_company()
	branches = get_effective_branch_list(frappe.session.user, company)
	if branch:
		branches = [branch]

	emp_filters, empty = _scoped_filters(company, branches)
	if empty:
		return _empty_pack(company, branch)

	headcount = frappe.db.count("Employee", emp_filters)
	branch_filter = emp_filters.get("branch")

	# Attendance / productivity (last 30 days)
	from frappe.utils import add_days

	start = add_days(today(), -30)
	att_filters = {"attendance_date": [">=", start], "status": "Present"}
	if company:
		att_filters["company"] = company
	if branch_filter:
		att_filters["branch"] = branch_filter

	present_days = frappe.db.count("HR Attendance", att_filters)
	attendance_rate = round(present_days / max(headcount * 22, 1) * 100, 1)

	# Leave
	open_leave = frappe.db.count("HR Leave Application", {**_hr_scope(company, branch_filter, "HR Leave Application"), "status": "Submitted"})

	# Recruitment
	open_reqs = frappe.db.count("HR Recruitment Request", {**_hr_scope(company, None, "HR Recruitment Request"), "status": ["in", ["Open", "In Progress"]]})
	pipeline = frappe.db.count("HR Job Applicant", {**_hr_scope(company, branch_filter, "HR Job Applicant"), "status": ["in", ["Open", "Screening", "Interview"]]})

	# Training (L&D hours proxy)
	training_count = frappe.db.count("HR Training Record", _hr_scope(company, branch_filter, "HR Training Record"))

	# Payroll cost proxy
	payroll_filters: dict = {"docstatus": 1}
	if company:
		payroll_filters["company"] = company
	if branch_filter:
		payroll_filters["branch"] = branch_filter
	slips = frappe.get_all("HR Salary Slip", filters=payroll_filters, pluck="net_pay")
	payroll_total = sum(flt(v) for v in slips)

	metrics = {
		"compliance_ethics": {
			"label": "Compliance & Ethics",
			"indicators": [
				{"kpi": "Active policies (Leave Types)", "value": frappe.db.count("HR Leave Type", {"company": company} if company else {})},
				{"kpi": "Pending leave approvals", "value": open_leave},
			],
		},
		"costs": {
			"label": "Costs",
			"indicators": [
				{"kpi": "Headcount", "value": headcount},
				{"kpi": "Payroll disbursed (net)", "value": flt(payroll_total, 2)},
				{"kpi": "Cost per FTE (payroll/FTE)", "value": round(flt(payroll_total) / max(headcount, 1), 2)},
			],
		},
		"diversity": {
			"label": "Diversity",
			"indicators": [
				{"kpi": "Employment types tracked", "value": _employment_mix(emp_filters)},
			],
		},
		"leadership": {
			"label": "Leadership",
			"indicators": [
				{"kpi": "Departments with heads", "value": _departments_with_heads(company, branch_filter)},
			],
		},
		"culture": {
			"label": "Organizational Culture",
			"indicators": [
				{"kpi": "Appraisals (total)", "value": frappe.db.count("HR Employee Appraisal", _hr_scope(company, branch_filter, "HR Employee Appraisal"))},
			],
		},
		"health_safety": {
			"label": "Health, Safety & Well-being",
			"indicators": [
				{"kpi": "Remote work days (30d)", "value": frappe.db.count("HR Attendance", {**att_filters, "status": "Remote"})},
				{"kpi": "On leave days (30d)", "value": frappe.db.count("HR Attendance", {**att_filters, "status": "On Leave"})},
			],
		},
		"productivity": {
			"label": "Productivity",
			"indicators": [
				{"kpi": "Attendance rate % (30d)", "value": attendance_rate},
				{"kpi": "Avg working hours", "value": _avg_working_hours(company, branch_filter, start)},
			],
		},
		"recruitment_mobility": {
			"label": "Recruitment & Mobility",
			"indicators": [
				{"kpi": "Open requisitions", "value": open_reqs},
				{"kpi": "Active applicants", "value": pipeline},
				{"kpi": "Interviews scheduled", "value": frappe.db.count("HR Interview", _hr_scope(company, branch_filter, "HR Interview"))},
			],
		},
		"skills": {
			"label": "Skills & Capabilities",
			"indicators": [
				{"kpi": "Training records", "value": training_count},
			],
		},
		"succession": {
			"label": "Succession Planning",
			"indicators": [
				{"kpi": "Employees with manager set", "value": _employees_with_manager(emp_filters)},
			],
		},
		"workforce_availability": {
			"label": "Workforce Availability",
			"indicators": [
				{"kpi": "Active headcount", "value": headcount},
				{"kpi": "Leave applications (YTD)", "value": _leave_ytd(company, branch_filter)},
				{"kpi": "Leave balance records", "value": frappe.db.count("HR Leave Balance", _hr_scope(company, branch_filter, "HR Leave Balance"))},
			],
		},
	}

	return {
		"standard": "ISO 30414:2018",
		"company": company,
		"branch": branch,
		"scope": {"company": company, "branch": branch},
		"generated_on": today(),
		"areas": metrics,
		"summary": {
			"headcount": headcount,
			"attendance_rate_30d": attendance_rate,
			"open_leave_approvals": open_leave,
			"active_applicants": pipeline,
		},
	}


def _hr_scope(company, branch_filter, doctype: str | None = None):
	f: dict = {}
	if not doctype:
		if company:
			f["company"] = company
		if branch_filter:
			f["branch"] = branch_filter
		return f

	meta = frappe.get_meta(doctype)
	if company and meta.has_field("company"):
		f["company"] = company
	if branch_filter and meta.has_field("branch"):
		f["branch"] = branch_filter
	return f


def _employment_mix(emp_filters: dict) -> int:
	if not frappe.db.has_column("Employee", "employment_type"):
		return 0
	types = frappe.get_all("Employee", filters=emp_filters, pluck="employment_type", distinct=True)
	return len([t for t in types if t])


def _departments_with_heads(company, branch_filter) -> int:
	f = _hr_scope(company, branch_filter, "HR Department")
	f["department_head"] = ["is", "set"]
	return frappe.db.count("HR Department", f)


def _employees_with_manager(emp_filters: dict) -> int:
	f = dict(emp_filters)
	if frappe.db.has_column("Employee", "reports_to"):
		f["reports_to"] = ["is", "set"]
		return frappe.db.count("Employee", f)
	if frappe.db.has_column("Employee", "manager"):
		f["manager"] = ["is", "set"]
		return frappe.db.count("Employee", f)
	return 0


def _avg_working_hours(company, branch_filter, start) -> float:
	filters: dict = {"attendance_date": [">=", start], "working_hours": [">", 0]}
	if company:
		filters["company"] = company
	if branch_filter:
		filters["branch"] = branch_filter
	hours = frappe.get_all("HR Attendance", filters=filters, pluck="working_hours")
	if not hours:
		return 0.0
	return round(sum(flt(h) for h in hours) / len(hours), 2)


def _leave_ytd(company, branch_filter) -> int:
	year = getdate(today()).year
	f = _hr_scope(company, branch_filter, "HR Leave Application")
	f["from_date"] = [">=", f"{year}-01-01"]
	return frappe.db.count("HR Leave Application", f)


def _empty_pack(company, branch):
	return {
		"standard": "ISO 30414:2018",
		"company": company,
		"branch": branch,
		"areas": {},
		"summary": {"headcount": 0},
	}


@frappe.whitelist()
def export_iso30414_json(company: str | None = None, branch: str | None = None) -> dict:
	return get_iso30414_metrics(company, branch)
