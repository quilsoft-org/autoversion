#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from subprocess import check_output, CalledProcessError

MANIFEST_RE = re.compile(r"['\"]version['\"]\s*:\s*['\"](.+?)['\"]")


def get_staged_files():
    """Get the list of staged files (cached)."""
    out = check_output(["git", "diff", "--cached", "--name-only"]).decode()
    return [Path(f) for f in out.splitlines() if f.strip()]


def extract_module_name(filepath: Path):
    """Detect module name from path (addons/modulename/...)."""
    try:
        parts = filepath.parts
        idx = parts.index("addons") + 1
        return parts[idx]
    except ValueError:
        return filepath.parts[0]


def get_version_from_file(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
        match = MANIFEST_RE.search(text)
        return match.group(1) if match else None
    except Exception:
        return None


def get_version_from_git(path: Path):
    """Get version of manifest from HEAD (before staged changes)."""
    try:
        out = check_output(["git", "show", f"HEAD:{path}"]).decode()
        match = MANIFEST_RE.search(out)
        return match.group(1) if match else None
    except CalledProcessError:
        return None  # file may not exist in HEAD (new module)


def main():
    print("🔍 Checking staged files for Odoo module version updates...")

    files = get_staged_files()
    print(f"Found {len(files)} staged files.")

    # Detect modules with XML/CSV changes
    touched_modules = {
        extract_module_name(f)
        for f in files
        if f.suffix in [".xml", ".csv"]
    }

    if not touched_modules:
        print("✅ No XML/CSV changes found. Nothing to check.")
        return 0

    print(f"Modules with XML/CSV changes: {', '.join(touched_modules)}")

    offending = []
    for module in touched_modules:
        manifest_path = Path(module) / "__manifest__.py"
        if not manifest_path.exists():
            offending.append(module)
            continue

        old_version = get_version_from_git(manifest_path)
        new_version = get_version_from_file(manifest_path)

        if old_version == new_version:
            offending.append(module)

    if offending:
        print("\n❌ These modules changed XML/CSV but did not bump version:")
        for m in offending:
            print(f"  - {m}")
        print(
            "\n⚠️  Remember to bump the version in __manifest__.py "
            "so Odoo.sh will reinstall the module."
        )
        return 1

    print("✅ All modules with XML/CSV changes have bumped their version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
