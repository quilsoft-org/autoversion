# autoversion

Pre-commit hook that checks if, when **any file** inside an Odoo module
(`addons/<module>/...`) is modified, the `version` in the corresponding
`__manifest__.py` is bumped to a strictly greater value.

## Requirements
- Python >= 3.10
- git

## What does it do?

For every staged file under `addons/<module>/`, it requires that the module's
`__manifest__.py` declares a version in the fixed format
`<odoo_major>.<odoo_minor>.<major>.<minor>.<patch>` — 5 numeric segments: 2
for the Odoo series plus 3 for the module version (e.g. `15.0.1.2.3`) —
**greater** than the one in `HEAD`. If not, the commit is blocked.

Rules:

- The new version must be **strictly greater** than the previous one
  (downgrades and same-version rewrites are rejected).
- The version must have **exactly 5 numeric segments** (`15.0.1.2.3`):
  2 for the Odoo series + 3 for the module version. Short versions like
  `15.0.1` or long ones are rejected; so are non-numeric suffixes like
  `rc1`, `alpha`, etc.
- A **new module** (manifest not yet in `HEAD`) only needs a valid version; no
  bump is required.
- A change in the Odoo **series** (first two segments, e.g. `16.0` -> `17.0`)
  is allowed but emits a warning.
- Files outside `addons/` (or directly under `addons/`) are ignored.

## Installation and usage with pre-commit

1. Add this repository to your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/your_user/autoversion
  rev: v1.2.0  # Use the appropriate version/tag
  hooks:
    - id: autoversion
```

2. Install pre-commit if you don't have it:

```bash
pip install pre-commit
```

3. Install the hooks in your repository:

```bash
pre-commit install
```

## Development

Run the tests:

```bash
python -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python -m pytest
```
