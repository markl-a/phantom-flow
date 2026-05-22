# Internal / one-off scripts

Ad-hoc scripts used during development for analysis, validation, or one-time generation. **Not part of the public API or supported user workflow.**

If a contributor wants to repeat one of these checks, the scripts are here as reference. Don't expect them to be polished or kept in sync with the main code.

## What's in here

| Script | What it does |
|---|---|
| `analyze_imports.py` | One-off scan of import graph |
| `check_dependencies.py` / `final_dependency_check.py` | Two iterations of the dep-audit script (output went to `docs/internal/DEPENDENCY_AUDIT_REPORT.md`) |
| `verify_project.py` | One-shot project-wide verification harness |
| `validation_real_world_examples.py` | Demo / e2e validation against real LLM endpoints (needs API keys) |

For the user-facing CLI / library, see the main `ai_automation_framework/` package and the project [README](../../README.md).
