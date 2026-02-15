#!/usr/bin/env python3
"""Golden rules linter for Parlo codebase.

Enforces critical architectural invariants with agent-readable error messages.
Each rule outputs pass/fail with file:line and fix instructions.
Exit code 1 on any failure.

Rules:
1. No raw SQL in services
2. File size limit (2000 lines)
3. Import layering (services must not import from api)
4. Simulation layer protected
5. Traced services (key service files have @traced)
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
SERVICES_DIR = APP_DIR / "services"

errors: list[str] = []


# --- Rule 1: No raw SQL in services ---


def check_no_raw_sql():
    """Service files should not use raw SQL via text() or string queries."""
    for py_file in sorted(SERVICES_DIR.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        content = py_file.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            # Check for sqlalchemy text() usage
            if re.search(r"\btext\s*\(", line) and "from sqlalchemy" not in line:
                # Verify it's actually sqlalchemy text, not some other text()
                if "import" not in line and "#" not in line.split("text(")[0]:
                    errors.append(
                        f"{py_file.relative_to(ROOT)}:{i}: Raw SQL via text() detected. "
                        f"FIX: Use SQLAlchemy ORM queries instead of raw SQL"
                    )


# --- Rule 2: File size limit ---


def check_file_size():
    """No single Python file should exceed 2000 lines."""
    max_lines = 2000
    for py_file in sorted(APP_DIR.rglob("*.py")):
        lines = len(py_file.read_text().splitlines())
        if lines > max_lines:
            errors.append(
                f"{py_file.relative_to(ROOT)}: {lines} lines (max {max_lines}). "
                f"FIX: Split into smaller modules — see docs/conventions.md#file-size"
            )


# --- Rule 3: Import layering ---


def check_import_layering():
    """app/services/ should not import from app/api/."""
    for py_file in sorted(SERVICES_DIR.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        content = py_file.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"from\s+app\.api", stripped) or re.search(r"import\s+app\.api", stripped):
                errors.append(
                    f"{py_file.relative_to(ROOT)}:{i}: Service imports from API layer. "
                    f"FIX: Services must not depend on API layer — see docs/architecture.md#layering"
                )


# --- Rule 4: Simulation layer protected ---


def check_simulation_protected():
    """simulate.py must exist and import MessageRouter."""
    simulate_path = APP_DIR / "api" / "v1" / "simulate.py"
    if not simulate_path.exists():
        errors.append(
            "app/api/v1/simulate.py does not exist. "
            "FIX: Simulation layer must stay functional — see docs/testing.md"
        )
        return

    content = simulate_path.read_text()
    if "MessageRouter" not in content:
        errors.append(
            "app/api/v1/simulate.py does not reference MessageRouter. "
            "FIX: Simulation must use the real MessageRouter — see docs/testing.md"
        )


# --- Rule 5: Traced services ---

KEY_SERVICE_FILES = [
    "message_router.py",
    "conversation.py",
    "onboarding.py",
    "customer_flows.py",
    "handoff.py",
    "staff_onboarding.py",
    "scheduling.py",
]


def check_traced_services():
    """Key service files should import and use @traced decorator."""
    for filename in KEY_SERVICE_FILES:
        filepath = SERVICES_DIR / filename
        if not filepath.exists():
            continue
        content = filepath.read_text()
        if "@traced" not in content:
            errors.append(
                f"app/services/{filename}: Missing @traced decorator usage. "
                f"FIX: Add @traced decorator to public functions — see docs/conventions.md#observability"
            )


def main():
    print("Checking golden rules...")

    check_no_raw_sql()
    check_file_size()
    check_import_layering()
    check_simulation_protected()
    check_traced_services()

    if errors:
        print(f"\n{len(errors)} violation(s) found:\n")
        for error in errors:
            print(f"  FAIL: {error}")
        sys.exit(1)
    else:
        print("All golden rules passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
