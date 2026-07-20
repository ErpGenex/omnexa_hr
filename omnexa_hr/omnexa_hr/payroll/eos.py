# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""
End-of-service / gratuity helpers.

IMPORTANT: Rules vary by contract, notice, and labour law updates. Values are **illustrative**
implementations for ERP accrual workflows — always validate with qualified legal / payroll advisors.

References (high level, not exhaustive):
- UAE: Federal Decree-Law No. 33 of 2021 — limited/unlimited gratuity patterns (21/30 days tiers, caps).
- KSA: Labour Law — employer vs employee termination and service-length fractions.
"""

from frappe.utils import flt


def compute_gratuity(
	*,
	service_days: int,
	daily_wage: float,
	monthly_salary: float = 0.0,
	scheme: str = "GENERIC_LIMITED",
) -> float:
	if service_days <= 0:
		return 0.0
	years = service_days / 365.0
	M = flt(monthly_salary)
	D = flt(daily_wage)

	if scheme in ("GENERIC_LIMITED", "UAE_LIMITED"):
		if D <= 0:
			return 0.0
		return _uae_limited_daily(years, D, apply_two_year_wage_cap=True)

	if scheme == "UAE_UNLIMITED":
		if D <= 0:
			return 0.0
		return _uae_limited_daily(years, D, apply_two_year_wage_cap=False)

	if scheme == "KSA_EMPLOYER_TERMINATION":
		if M <= 0:
			return 0.0
		return flt(_ksa_employer_full_entitlement(years, M), 2)

	if scheme == "KSA_EMPLOYEE_RESIGNATION":
		if M <= 0:
			return 0.0
		base = _ksa_employer_full_entitlement(years, M)
		return flt(_ksa_resignation_fraction(years, base), 2)

	if scheme == "CUSTOM":
		# Placeholder: treat like generic until manual override DocType is added.
		if D <= 0:
			return 0.0
		return _uae_limited_daily(years, D, apply_two_year_wage_cap=True)

	if D <= 0:
		return 0.0
	return _uae_limited_daily(years, D, apply_two_year_wage_cap=True)


def _uae_limited_daily(years: float, daily_wage: float, *, apply_two_year_wage_cap: bool) -> float:
	"""21 days wage/year for first 5 years, 30 days/year thereafter (daily wage basis)."""
	first_segment_years = min(years, 5.0)
	rest_years = max(years - 5.0, 0.0)
	raw = first_segment_years * 21.0 * daily_wage + rest_years * 30.0 * daily_wage
	if apply_two_year_wage_cap:
		cap = 24 * 30 * daily_wage
		return flt(min(raw, cap), 2)
	return flt(raw, 2)


def _ksa_employer_full_entitlement(years: float, monthly_salary: float) -> float:
	"""
	Simplified employer-initiated termination (illustrative):
	half-month salary per year for the first five years + one month per year thereafter.
	"""
	if years <= 0 or monthly_salary <= 0:
		return 0.0
	first = min(years, 5.0)
	rest = max(years - 5.0, 0.0)
	return first * (monthly_salary / 2.0) + rest * monthly_salary


def _ksa_resignation_fraction(years: float, full_entitlement: float) -> float:
	"""Common resignation fraction pattern (illustrative; actual law depends on tenure and notice)."""
	if years < 2:
		return 0.0
	if years < 5:
		return full_entitlement / 3.0
	if years < 10:
		return full_entitlement * (2.0 / 3.0)
	return full_entitlement
