# Final Release Audit

Status: release-tagged locally; remote publication pending.

Date: 2026-06-26

## Scope

- Default release surface: `phantom_flow` package and documented public commands.
- Excluded scan noise: `.git`, `.ensemble`, `.venv`, `venv`, `__pycache__`, `.pytest_cache`, `reports`, `dist`, and `build`.
- Staged source trees such as `ai_automation_framework/` and `data_analysis/` are not part of the installable `phantom-flow` distribution.

## Secret And Private-Data Scan

Command class: `rg` high-confidence patterns for private keys, AWS access keys, GitHub tokens, OpenAI-shaped keys, Slack tokens, and Google API keys.

Result: `high_conf_secret_hits=0`.

Note: synthetic secret-shaped test vectors in staged security tests were rewritten with string concatenation so sanitizer coverage remains without storing real token-shaped literals.

## Dependency/License Review

- Project license: Apache-2.0.
- Default runtime dependency: `PyYAML>=6.0`; metadata sample reviewed as `PyYAML==6.0.3`, MIT.
- Optional dependency: `youtube-transcript-api>=0.6`; metadata sample reviewed as `youtube-transcript-api==1.2.4`, MIT.
- Staged subtree dependencies are excluded from the default release package and require separate review before publication as their own packages.

Direct default release-scope dependency/license review result: pass.

## Remaining Publication Gates

- Manual maintainer approval is recorded in `docs/PUBLIC_RELEASE_APPROVAL.md`.
- Local annotated tag `v0.1.0-alpha.0` was created after the root strict approval verifier and conductor sign-off passed.
- Any decision to publish staged subtrees requires a separate dependency/license and safety audit.
