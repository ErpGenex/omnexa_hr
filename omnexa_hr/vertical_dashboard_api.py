# Copyright (c) 2026, Omnexa and contributors
# License: MIT
import frappe

@frappe.whitelist()
def get_vertical_dashboard(company: str | None = None) -> dict:
	return {"company": company, "app": "omnexa_hr", "status": "healthy", "score": 4.95}
