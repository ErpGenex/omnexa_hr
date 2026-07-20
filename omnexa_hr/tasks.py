# Copyright (c) 2026, Omnexa and contributors
# License: See license.txt

from __future__ import annotations

import frappe
from frappe.utils import getdate, today


def process_leave_approval_escalations():
	"""Escalate pending leave applications past approval SLA."""
	current = getdate(today())
	rows = frappe.get_all(
		"HR Leave Application",
		filters={"docstatus": 0, "status": "Open", "from_date": ["<=", current]},
		fields=["name"],
		limit_page_length=500,
	)
	for row in rows:
		doc = frappe.get_doc("HR Leave Application", row.name)
		if doc.status != "Escalated":
			doc.status = "Escalated"
			doc.save(ignore_permissions=True)
