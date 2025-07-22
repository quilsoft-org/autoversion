#!/usr/bin/env python3
import re
import sys
from pathlib import Path

MODULE_RE = re.compile(r".*/([^/]+)/.*\.xml$")
MANIFEST_RE = re.compile(r"['\"]version['\"]\s*:\s*['\"](.+?)['\"]")


def get_staged_files():
    """Get the list of staged files (cached)"""
    from subprocess import check_output

    out = check_output(["git", "diff", "--cached", "--name-only"]).decode()
    return [f for f in out.splitlines() if f.strip()]


def extract_module_name(filepath: Path):
    try:
        parts = filepath.parts
        idx = parts.index("addons") + 1  # typical Odoo layout
        return parts[idx]
    except ValueError:
        # fallback: assume layout: ./modulename/...
        return filepath.parts[0]


def get_module_version(manifest_path: Path):
    try:
        text = manifest_path.read_text(encoding="utf-8")
        match = MANIFEST_RE.search(text)
        return match.group(1) if match else None
    except Exception:
        return None


def main():
    print("Checking staged files for Odoo module version updates...")

    files = get_staged_files()

    print(f"Found {len(files)} staged files.")
    
    xml_modules = set()
    manifest_versions = {}

    for file in files:
        p = Path(file)
        if not p.exists():
            continue

        if p.name == "__manifest__.py":
            module = extract_module_name(p)
            manifest_versions[module] = get_module_version(p)

        elif p.suffix in [".xml", ".csv"]:
            module = extract_module_name(p)
            xml_modules.add(module)

    offending = []
    for module in xml_modules:
        manifest_path = Path(module) / "__manifest__.py"
        old_version = (
            get_module_version(manifest_path) if manifest_path.exists() else None
        )
        staged_manifest = [f for f in files if f.endswith(f"{module}/__manifest__.py")]
        if not staged_manifest:
            offending.append(module)

    if offending:
        print("❌ These modules have changes in XML or CSV files but did not update the version:")
        for m in offending:
            print(f"  - {m}")
        print(
            "\n⚠️  Remember to bump the version in __manifest__.py so Odoo.sh will reinstall the module."
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
