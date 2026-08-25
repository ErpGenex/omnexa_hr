# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe


def seed_demo_biometric_device(company: str = "WIZ", branch: str = "WIZ-HO") -> dict:
	if not frappe.db.exists("DocType", "HR Biometric Device"):
		return {"created": False, "reason": "DocType missing"}
	if frappe.db.exists("HR Biometric Device", {"device_code": "DEMO-ZKT-WIZ-HO"}):
		return {"created": False, "reason": "already exists", "name": "DEMO-ZKT-WIZ-HO"}

	doc = frappe.get_doc(
		{
			"doctype": "HR Biometric Device",
			"device_name": "WIZ Head Office — Demo ZKTeco",
			"device_code": "DEMO-ZKT-WIZ-HO",
			"device_type": "ZKTeco",
			"ip_address": "192.168.1.201",
			"port": 4370,
			"company": company,
			"branch": branch,
			"is_active": 1,
			"sync_enabled": 0,
			"last_sync_status": "Demo device — enable sync when hardware is connected",
		}
	)
	doc.flags.ignore_branch_access = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"created": True, "name": doc.name}
