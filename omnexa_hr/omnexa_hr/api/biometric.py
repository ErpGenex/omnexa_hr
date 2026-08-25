# Copyright (c) 2026, Omnexa and contributors
# License: MIT

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime, getdate, now_datetime

from omnexa_core.omnexa_core.session_context import get_effective_branch_list, get_effective_company


def _match_field(device) -> str:
	return device.employee_match_field or frappe.db.get_single_value(
		"HR Settings", "default_employee_match_field"
	) or "biometric_user_id"


def _find_employee(raw_user_id: str, company: str, match_field: str) -> str | None:
	if not raw_user_id:
		return None
	if not frappe.db.has_column("Employee", match_field):
		match_field = "employee_code"
	return frappe.db.get_value("Employee", {match_field: raw_user_id, "company": company}, "name")


def import_punch(device_name: str, raw_user_id: str, punch_datetime: str, punch_type: str = "Unknown") -> dict:
	device = frappe.get_doc("HR Biometric Device", device_name)
	match_field = _match_field(device)
	employee = _find_employee(raw_user_id, device.company, match_field)
	doc = frappe.get_doc(
		{
			"doctype": "HR Biometric Punch Log",
			"device": device.name,
			"raw_user_id": raw_user_id,
			"punch_datetime": punch_datetime,
			"punch_type": punch_type or "Unknown",
			"employee": employee,
			"employee_name": frappe.db.get_value("Employee", employee, "employee_name") if employee else None,
		}
	)
	doc.insert(ignore_permissions=True)
	return {"name": doc.name, "employee": employee}


def process_unprocessed_punches(limit: int = 500) -> dict:
	punches = frappe.get_all(
		"HR Biometric Punch Log",
		filters={"processed": 0, "employee": ["is", "set"]},
		fields=["name", "employee", "employee_name", "punch_datetime", "punch_type", "device", "company", "branch"],
		order_by="punch_datetime asc",
		limit=limit,
	)
	processed = 0
	for row in punches:
		try:
			_apply_punch_to_attendance(row)
			frappe.db.set_value("HR Biometric Punch Log", row.name, "processed", 1, update_modified=True)
			processed += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"Biometric punch {row.name}")
	return {"processed": processed, "total": len(punches)}


def _apply_punch_to_attendance(punch: dict):
	attendance_date = getdate(punch.punch_datetime)
	attendance_name = frappe.db.get_value(
		"HR Attendance",
		{"employee": punch.employee, "attendance_date": attendance_date},
		"name",
	)
	if attendance_name:
		doc = frappe.get_doc("HR Attendance", attendance_name)
	else:
		employee = frappe.db.get_value(
			"Employee", punch.employee, ["company", "branch", "employee_name"], as_dict=True
		)
		doc = frappe.get_doc(
			{
				"doctype": "HR Attendance",
				"employee": punch.employee,
				"employee_name": employee.employee_name,
				"company": employee.company,
				"branch": employee.branch or punch.branch,
				"attendance_date": attendance_date,
				"status": "Present",
				"attendance_source": "Biometric",
				"biometric_device": punch.device,
			}
		)

	punch_dt = get_datetime(punch.punch_datetime)
	if punch.punch_type == "IN" or (not doc.check_in and punch.punch_type == "Unknown"):
		if not doc.check_in or punch_dt < get_datetime(doc.check_in):
			doc.check_in = punch_dt
	elif punch.punch_type == "OUT" or punch.punch_type == "Unknown":
		if not doc.check_out or punch_dt > get_datetime(doc.check_out):
			doc.check_out = punch_dt

	doc.attendance_source = "Biometric"
	doc.biometric_device = punch.device
	doc.flags.ignore_permissions = True
	if doc.is_new():
		doc.insert()
	else:
		doc.save()

	frappe.db.set_value("HR Biometric Punch Log", punch.name, "hr_attendance", doc.name, update_modified=False)


@frappe.whitelist()
def sync_all_devices() -> dict:
	if not frappe.db.get_single_value("HR Settings", "auto_sync_biometric"):
		return {"devices": 0, "message": "Auto sync disabled"}

	from omnexa_hr.omnexa_hr.services.biometric_device import pull_device_attendance

	devices = frappe.get_all("HR Biometric Device", filters={"is_active": 1}, pluck="name")
	device_results = []
	for device in devices:
		device_results.append(pull_device_attendance(device))

	result = process_unprocessed_punches()
	result["devices"] = len(devices)
	result["device_results"] = device_results
	return result


@frappe.whitelist()
def sync_single_device(device: str) -> dict:
	from omnexa_hr.omnexa_hr.services.biometric_device import sync_device

	return sync_device(device)


@frappe.whitelist()
def import_punch_from_desk(device: str, raw_user_id: str, punch_datetime: str, punch_type: str = "Unknown") -> dict:
	return import_punch(device, raw_user_id, punch_datetime, punch_type)
