# Copyright (c) 2026, Omnexa and contributors
# License: MIT

"""ZKTeco / biometric device drivers."""

from __future__ import annotations

from datetime import datetime

import frappe
from frappe.utils import get_datetime, now_datetime


def pull_device_attendance(device_name: str) -> dict:
	"""Fetch attendance from a biometric device and import punch logs."""
	device = frappe.get_doc("HR Biometric Device", device_name)
	if not device.is_active:
		return {"device": device_name, "imported": 0, "skipped": "inactive"}

	if device.device_type == "File Import":
		return {"device": device_name, "imported": 0, "message": "File Import — use manual import"}

	if device.device_type == "Manual":
		return {"device": device_name, "imported": 0, "message": "Manual device"}

	if device.device_type == "ZKTeco":
		return _pull_zkteco(device)

	if device.device_type in ("Hikvision", "Generic TCP"):
		return {
			"device": device_name,
			"imported": 0,
			"message": f"{device.device_type} driver pending — use import_punch API",
		}

	return {"device": device_name, "imported": 0, "message": "Unknown device type"}


def _pull_zkteco(device) -> dict:
	if not device.device_ip:
		return {"device": device.name, "imported": 0, "error": "Device IP required"}

	try:
		from zk import ZK
	except ImportError:
		return {
			"device": device.name,
			"imported": 0,
			"error": "pyzk not installed. Run: bench pip install pyzk",
		}

	port = int(device.device_port or 4370)
	conn = None
	imported = 0
	skipped = 0

	try:
		zk = ZK(device.device_ip, port=port, timeout=10)
		conn = zk.connect()
		conn.disable_device()
		records = conn.get_attendance() or []
		last_sync = device.last_sync

		from omnexa_hr.omnexa_hr.api.biometric import import_punch

		for rec in records:
			punch_dt = rec.timestamp
			if not punch_dt:
				continue
			if last_sync and get_datetime(punch_dt) <= get_datetime(last_sync):
				skipped += 1
				continue

			raw_id = str(rec.user_id)
			punch_type = "IN" if getattr(rec, "punch", None) in (0, "0", None) else "OUT"
			existing = frappe.db.exists(
				"HR Biometric Punch Log",
				{
					"device": device.name,
					"raw_user_id": raw_id,
					"punch_datetime": punch_dt,
				},
			)
			if existing:
				skipped += 1
				continue

			import_punch(device.name, raw_id, str(punch_dt), punch_type)
			imported += 1

		conn.test_voice()
	except Exception as exc:
		frappe.log_error(frappe.get_traceback(), f"ZKTeco sync {device.name}")
		return {"device": device.name, "imported": imported, "error": str(exc)}
	finally:
		if conn:
			try:
				conn.enable_device()
				conn.disconnect()
			except Exception:
				pass

	frappe.db.set_value("HR Biometric Device", device.name, "last_sync", now_datetime(), update_modified=True)
	return {"device": device.name, "imported": imported, "skipped": skipped}


def sync_device(device_name: str) -> dict:
	result = pull_device_attendance(device_name)
	from omnexa_hr.omnexa_hr.api.biometric import process_unprocessed_punches

	process_result = process_unprocessed_punches()
	result["attendance_processed"] = process_result.get("processed", 0)
	return result
