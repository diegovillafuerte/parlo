#!/usr/bin/env python3
"""Validate documentation structure and cross-references.

Checks:
1. All files listed in CLAUDE.md Documentation Map exist
2. CLAUDE.md is under 200 lines
3. Each docs/ file has a # Title header
4. Internal cross-references (docs/foo.md) point to existing files
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_MD = ROOT / "CLAUDE.md"
DOCS_DIR = ROOT / "docs"
MAX_CLAUDE_LINES = 200

errors: list[str] = []


def check_claude_md_size():
    """Check CLAUDE.md is under MAX_CLAUDE_LINES lines."""
    lines = CLAUDE_MD.read_text().splitlines()
    if len(lines) > MAX_CLAUDE_LINES:
        errors.append(
            f"CLAUDE.md is {len(lines)} lines (max {MAX_CLAUDE_LINES}). "
            f"FIX: Move detailed content to docs/ files — see docs/conventions.md"
        )


def check_documentation_map():
    """Check all files in the Documentation Map table exist."""
    content = CLAUDE_MD.read_text()
    # Match markdown table rows like: | `docs/foo.md` | description |
    pattern = re.compile(r"\|\s*`(docs/\S+)`\s*\|")
    for match in pattern.finditer(content):
        doc_path = ROOT / match.group(1)
        if not doc_path.exists():
            errors.append(
                f"Documentation Map references '{match.group(1)}' but file does not exist. "
                f"FIX: Create the file or remove it from the Documentation Map in CLAUDE.md"
            )


def check_doc_headers():
    """Check each docs/ markdown file has a # Title header."""
    for md_file in sorted(DOCS_DIR.glob("*.md")):
        content = md_file.read_text().strip()
        if not content.startswith("# "):
            errors.append(
                f"{md_file.relative_to(ROOT)} is missing a '# Title' header. "
                f"FIX: Add a title as the first line of the file"
            )


def check_cross_references():
    """Check internal cross-references in all docs/ and CLAUDE.md files."""
    files_to_check = [CLAUDE_MD] + list(DOCS_DIR.glob("*.md"))
    pattern = re.compile(r"`(docs/\S+\.md)`|See\s+`(docs/\S+\.md)`")

    for filepath in files_to_check:
        content = filepath.read_text()
        for match in pattern.finditer(content):
            ref = match.group(1) or match.group(2)
            target = ROOT / ref
            if not target.exists():
                errors.append(
                    f"{filepath.relative_to(ROOT)} references '{ref}' but file does not exist. "
                    f"FIX: Create the file or fix the reference"
                )


def main():
    print("Validating documentation structure...")

    check_claude_md_size()
    check_documentation_map()
    check_doc_headers()
    check_cross_references()

    if errors:
        print(f"\n{len(errors)} error(s) found:\n")
        for error in errors:
            print(f"  ERROR: {error}")
        sys.exit(1)
    else:
        print("All documentation checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
