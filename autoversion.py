#!/usr/bin/env python3
"""Pre-commit hook: require a version bump in __manifest__.py when any file
inside an Odoo module (addons/<module>/...) is modified."""

import re
import sys
from pathlib import Path
from subprocess import CalledProcessError, check_output

MANIFEST_RE = re.compile(r"['\"]version['\"]\s*:\s*['\"](.+?)['\"]")

ADDONS_DIR = "addons"

# Version format: <odoo_major>.<odoo_minor>.<major>.<minor>.<patch>
SERIES_SEGMENTS = 2   # Odoo series, e.g. "15.0"
MODULE_SEGMENTS = 3   # module version, e.g. "1.2.3"
VERSION_SEGMENTS = SERIES_SEGMENTS + MODULE_SEGMENTS  # 5


def get_staged_files():
    """Staged files as repo-root-relative paths (from git)."""
    out = check_output(["git", "diff", "--cached", "--name-only"]).decode()
    return [Path(f) for f in out.splitlines() if f.strip()]


def module_dir_from_path(path):
    """Return addons/<module> for files in a flat addons/<module>/... layout.

    Returns None for files outside addons/ or directly under addons/.
    """
    parts = path.parts
    if len(parts) < 3 or parts[0] != ADDONS_DIR:
        return None
    return Path(parts[0]) / parts[1]


def get_version_from_file(path):
    """Read the 'version' field from a manifest file, or None."""
    try:
        match = MANIFEST_RE.search(path.read_text(encoding="utf-8"))
        return match.group(1) if match else None
    except (OSError, UnicodeDecodeError):
        return None


def get_version_from_git(path):
    """Version of the manifest at HEAD (before staged changes)."""
    try:
        out = check_output(["git", "show", f"HEAD:{path}"]).decode()
        match = MANIFEST_RE.search(out)
        return match.group(1) if match else None
    except CalledProcessError:
        return None  # file not in HEAD (new module)


def parse_version(version):
    """Parse a full version into a tuple of ints, or None.

    Requires exactly VERSION_SEGMENTS numeric segments: 2 for the Odoo
    series + 3 for the module version (e.g. 15.0.1.2.3).
    """
    if not version:
        return None
    parts = version.split(".")
    if len(parts) != VERSION_SEGMENTS:
        return None
    if not all(part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)


def is_greater(new, old):
    """True if new > old (both must already parse to the same fixed shape)."""
    new_t = parse_version(new)
    old_t = parse_version(old)
    if new_t is None or old_t is None:
        return None
    return new_t > old_t


def series(version):
    """First two numeric segments (Odoo series), e.g. (16, 0)."""
    return tuple(int(part) for part in version.split(".")[:2])


def main():
    files = get_staged_files()

    touched = set()
    for f in files:
        module_dir = module_dir_from_path(f)
        if module_dir is not None:
            touched.add(module_dir)

    if not touched:
        print("No Odoo module files staged. Nothing to check.")
        return 0

    offending = []
    warnings = []

    for module_dir in sorted(touched):
        module_name = module_dir.parts[1]
        manifest = module_dir / "__manifest__.py"

        if not manifest.exists():
            offending.append(f"{module_name}: __manifest__.py not found")
            continue

        new_version = get_version_from_file(manifest)
        if new_version is None:
            offending.append(
                f"{module_name}: no 'version' field in __manifest__.py"
            )
            continue

        if parse_version(new_version) is None:
            offending.append(
                f"{module_name}: version '{new_version}' is invalid "
                f"(expected {VERSION_SEGMENTS} numeric segments: "
                f"{SERIES_SEGMENTS} for the Odoo series + "
                f"{MODULE_SEGMENTS} for the module version, e.g. 15.0.1.2.3)"
            )
            continue

        old_version = get_version_from_git(manifest)
        if old_version is None:
            continue  # new module: no bump required

        if parse_version(old_version) is None:
            warnings.append(
                f"{module_name}: previous version '{old_version}' is not "
                "numeric; cannot verify the bump"
            )
            continue

        if not is_greater(new_version, old_version):
            offending.append(
                f"{module_name}: version not bumped "
                f"({old_version} -> {new_version})"
            )
            continue

        if series(new_version) != series(old_version):
            warnings.append(
                f"{module_name}: Odoo series changed "
                f"({'.'.join(map(str, series(old_version)))} -> "
                f"{'.'.join(map(str, series(new_version)))})"
            )

    for message in warnings:
        print(f"⚠️  WARNING: {message}")

    if offending:
        print("\n❌ These modules changed but did not bump their version:")
        for message in offending:
            print(f"  - {message}")
        print(
            "\nBump the 'version' in __manifest__.py "
            "so Odoo.sh reinstalls the module."
        )
        return 1

    print("✅ All touched modules bumped their version.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
