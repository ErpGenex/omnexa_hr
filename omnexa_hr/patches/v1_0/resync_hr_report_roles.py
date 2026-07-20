# Copyright (c) 2026, Omnexa and contributors
# License: MIT. See license.txt

"""Re-apply HR report role assignments (idempotent) when REPORT_NAMES list grows."""


def execute():
	from omnexa_hr.patches.v1_0.sync_hr_report_roles import execute as sync_execute

	sync_execute()
