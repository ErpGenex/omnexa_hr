# Copyright (c) 2026, Omnexa
"""Strip ERP/finance links from HR workspace (one-time cleanup)."""

import frappe


def execute():
	if not frappe.db.exists("Workspace", "HR"):
		return
	from omnexa_hr.workspace.hr_workspace import sync_hr_workspace_menu

	sync_hr_workspace_menu(save=True, rebuild=True)
	frappe.clear_cache(doctype="Workspace")
