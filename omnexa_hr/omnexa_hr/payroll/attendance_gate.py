# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _
from frappe.utils import getdate

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled


def validate_attendance_for_salary_slip(doc):
	"""Optional gate: require at least one Present/Remote attendance row in period."""
	if not is_feature_enabled("global_hr_payroll_require_attendance", False):
		return
	if doc.skip_attendance_check:
		return
	if not doc.employee or not doc.period_start or not doc.period_end:
		return
	start = getdate(doc.period_start)
	end = getdate(doc.period_end)
	if end < start:
		frappe.throw(_("Period End cannot be before Period Start."), title=_("Salary Slip"))
	days = (end - start).days + 1
	if days <= 3:
		return
	count = frappe.db.count(
		"HR Attendance",
		filters={
			"employee": doc.employee,
			"company": doc.company,
			"attendance_date": ["between", [start, end]],
			"status": ["in", ["Present", "Remote"]],
		},
	)
	if count < 1:
		frappe.throw(
			_("No Present/Remote attendance found for this employee in the pay period. Enable Skip attendance gate only if authorised."),
			title=_("Attendance"),
		)
