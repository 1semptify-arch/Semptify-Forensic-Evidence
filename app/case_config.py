"""Per-case configuration for the forensic evidence system.

Values here are loaded from environment variables when available so the same
codebase can be reused across different cases. If no environment variables are
set, it falls back to a configurable default.
"""

import os

CASE_NAME = os.getenv("FORENSIC_CASE_NAME", "default")
CASE_TITLE = os.getenv("FORENSIC_CASE_TITLE", "Active Case")
CASE_NUMBER = os.getenv("FORENSIC_CASE_NUMBER", "CASE-001")

CASES_DIR = os.getenv("FORENSIC_CASES_DIR", "data/cases")
DEFAULT_CASE_DIR = os.path.join(CASES_DIR, CASE_NAME.replace(" ", "_").lower())
