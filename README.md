# autoversion

Pre-commit plugin that checks if, when XML or CSV files are modified in a module, the version in the corresponding __manifest__.py file is also updated.

## Requirements
- Python >= 3.10
- git

## Installation and usage with pre-commit

1. Add this repository to your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/your_user/autoversion
  rev: v1.0.4  # Use the appropriate version/tag
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

## What does it do?

- If you modify XML or CSV files in a module and do not update the version in `__manifest__.py`, the commit will be blocked and a warning message will be shown.
