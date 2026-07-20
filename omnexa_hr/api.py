# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

import frappe
from frappe import _

from omnexa_core.omnexa_core.feature_flags import is_feature_enabled

from omnexa_hr.omnexa_hr.payroll.eos import compute_gratuity


@frappe.whitelist()
def hr_payroll_feature_flags():
	return {
		"global_hr_payroll_require_attendance": is_feature_enabled("global_hr_payroll_require_attendance", False),
		"global_hr_payroll_auto_accrual_je": is_feature_enabled("global_hr_payroll_auto_accrual_je", True)}


@frappe.whitelist()
def preview_end_of_service(employee: str, termination_date: str, last_basic_salary: float | str | None = None, scheme: str = "UAE_LIMITED"):
	"""Return estimated gratuity without saving (configure schemes per jurisdiction)."""
	if not frappe.db.exists("Employee", employee):
		frappe.throw(_("Employee not found."), title=_("EOS"))
	if last_basic_salary in (None, ""):
		frappe.throw(_("Last basic salary is required."), title=_("EOS"))
	from frappe.utils import flt, getdate

	joining = frappe.db.get_value("Employee", employee, "date_of_joining")
	td = getdate(termination_date)
	service_days = 0
	if joining:
		jd = getdate(joining)
		if td >= jd:
			service_days = (td - jd).days
	monthly = flt(last_basic_salary)
	daily = monthly / 30.0 if monthly else 0.0
	use_scheme = (scheme or "UAE_LIMITED").strip()
	return {
		"service_days": service_days,
		"daily_wage": daily,
		"monthly_salary": monthly,
		"scheme": use_scheme,
		"gratuity_amount": compute_gratuity(
			service_days=service_days,
			daily_wage=daily,
			monthly_salary=monthly,
			scheme=use_scheme,
		)}

@frappe.whitelist()
def preview_sector_kpi(scenario: str | None = None, params: str | None = None) -> dict:
	"""SAP Wave C — sector KPI preview (omnexa_core bridge)."""
	from omnexa_core.omnexa_core.vertical_api import preview_sector_kpi as _core_preview

	return _core_preview("hr", scenario=scenario, params=params)

