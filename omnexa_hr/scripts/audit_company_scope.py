#!/usr/bin/env python3
"""Audit company/branch scoping — omnexa_hr."""
from __future__ import annotations

import frappe

from omnexa_core.omnexa_core.api_scope import get_api_scope


def run():
	scope = get_api_scope()
	return {
		"ok": True,
		"app": "omnexa_hr",
		"company": scope.get("company"),
		"branch": scope.get("branch"),
		"uses_session_context": bool(scope.get("company")),
	}
