# Copyright (c) 2026, Omnexa and contributors
# License: MIT
import json, os
import frappe
from frappe.utils import get_bench_path
from omnexa_hr.hr_gap_register import get_gap_status
from omnexa_hr.hr_global_benchmark import get_global_hr_score

@frappe.whitelist()
def export_hr_global_audit() -> dict:
	root = os.path.join(get_bench_path(), "Docs", "2026-06-06_OMNEXA_HR_GLOBAL_AUDIT")
	os.makedirs(root, exist_ok=True)
	score, gaps = get_global_hr_score(), get_gap_status()
	for n, d in (("LIVE_SCORE.json", score), ("GAP_REGISTER.json", gaps)):
		with open(os.path.join(root, n), "w", encoding="utf-8") as fh:
			json.dump(d, fh, ensure_ascii=False, indent=2)
	return {"path": root, "weighted_score": score.get("weighted_score"), "gaps_open": gaps.get("gaps_open")}
