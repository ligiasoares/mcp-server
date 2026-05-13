#!/usr/bin/env python3
"""
Apply boss edits back to content.json.

Usage:
    python3 apply_changes.py tontine_content_2026-05-13.html

The HTML file is the one downloaded by the boss from the editor.
Changes are merged into content.json. Restart the MCP server afterwards.
"""

import json
import pathlib
import re
import sys


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 apply_changes.py <boss_edited_file.html>")
        sys.exit(1)

    html_path = pathlib.Path(sys.argv[1])
    if not html_path.exists():
        print(f"File not found: {html_path}")
        sys.exit(1)

    html = html_path.read_text(encoding="utf-8")

    match = re.search(r'<script id="content-data" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        print("ERROR: No content data found in this file. Make sure you're using the correct editor HTML.")
        sys.exit(1)

    try:
        edits = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"ERROR: Could not parse content data: {e}")
        sys.exit(1)

    content_path = pathlib.Path(__file__).parent / "content.json"
    current = json.loads(content_path.read_text(encoding="utf-8"))

    changes = 0

    for uri, fields in edits.get("resources", {}).items():
        full_uri = f"tontine://{uri}"
        if full_uri not in current["resources"]:
            print(f"  SKIP: unknown resource '{full_uri}'")
            continue
        for field, value in fields.items():
            if isinstance(value, str) and value.strip():
                if current["resources"][full_uri].get(field) != value:
                    current["resources"][full_uri][field] = value
                    changes += 1
                    print(f"  UPDATED: {full_uri} → {field}")

    for code, fields in edits.get("asset_types", {}).items():
        if code not in current["asset_types"]:
            print(f"  SKIP: unknown asset type '{code}'")
            continue
        for field, value in fields.items():
            if isinstance(value, str) and value.strip():
                if current["asset_types"][code].get(field) != value:
                    current["asset_types"][code][field] = value
                    changes += 1
                    print(f"  UPDATED: {code} → {field}")

    if changes == 0:
        print("No changes detected — content.json unchanged.")
        return

    content_path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone — {changes} field(s) updated in content.json.")
    print("Restart the MCP server to apply: python3 server.py --http --port 8000")


if __name__ == "__main__":
    main()
