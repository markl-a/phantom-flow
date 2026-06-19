> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-flow.md;此為歷史版本。

# phantom-flow — Documentation Index

⭐ Single navigation entry for the repository's own documentation. For project
**status** (what is shipped / in progress / planned), see
[`../ROADMAP.md`](../ROADMAP.md) — it is the single source of truth; the docs
below describe *how* and *why*, not *when*.

> Scope: this index covers **phantom-flow's own docs**. The vendored subtrees
> `ai_automation_framework/` and `data_analysis/` carry their own (unmaintained
> here) documentation and are not part of the engine — see
> [`../DESIGN.md`](../DESIGN.md) §4.

## Current docs

| Document | Description | Authority |
|----------|-------------|-----------|
| [`../README.md`](../README.md) | Front door: positioning, install, quickstart, flow shape, the 9 native blocks. | Canonical entry point. |
| [`../ROADMAP.md`](../ROADMAP.md) | ⭐ Single status SSOT — Shipped / In progress / Planned-next, grounded in real commits. | **Authoritative for all status.** |
| [`../DESIGN.md`](../DESIGN.md) | As-built architecture: engine vs vendored subtrees, phantom-mesh integration, vendored-source integration plan (§4). | Canonical design rationale. |
| [`./06-phantom-flow.md`](06-phantom-flow.md) | Original product **vision / spec** (n8n-on-phantom-mesh positioning, competitor analysis, MVP scope). Aspirational — banner-marked; reality lives in README/ROADMAP. | Vision/spec (not as-built). |

## Archived

Frozen historical snapshots live in [`_archive/`](_archive/). They are kept for
provenance (never deleted) and carry an `ARCHIVED` tombstone. Do not treat them
as current — current status is always [`../ROADMAP.md`](../ROADMAP.md).

| Document | Description |
|----------|-------------|
| [`_archive/2026-05-22-tier1-initial-dev.md`](_archive/2026-05-22-tier1-initial-dev.md) | Dated dev-log from the Tier-1 subtree-merge + first runner. Superseded by README/ROADMAP/DESIGN. |
| [`_archive/AUDIT-flow-final.md`](_archive/AUDIT-flow-final.md) | Point-in-time gap audit (force_stub / LLMResult.error / http_get max_bytes). All three gaps are now fixed and shipped (see ROADMAP). |
