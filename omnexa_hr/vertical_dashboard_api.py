# Copyright (c) 2026, Omnexa and contributors
# License: MIT

import frappe

from omnexa_core.omnexa_core.api_scope import get_api_scope
from omnexa_core.omnexa_core.world_class import certify_app


@frappe.whitelist()
def get_vertical_dashboard(company: str | None = None) -> dict:
	scope = get_api_scope(company=company)
	cert = certify_app("omnexa_hr")
	return {
		"company": scope.get("company"),
		"branch": scope.get("branch"),
		"scope": scope,
		"app": "omnexa_hr",
		"status": "healthy",
		"score": cert["weighted_score"],
		"score_100": cert["score_100"],
		"certification_level": cert["certification_level"],
		"world_class_gate": cert["world_class_gate"],
		"uses_session_context": bool(scope.get("company")),
		"world_class": cert,
	}
