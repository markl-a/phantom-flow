# phantom-flow

[![CI](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)

> 極小、local-first、mesh-native 的 YAML 工作流執行器（phantom-mesh 生態系）。近乎純標準函式庫(唯一硬相依 PyYAML)；LLM 步驟可經 phantom-mesh 路由,缺 CLI 則退回決定性 stub。

## Quickstart

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m phantom_flow.runner --help
```

Validate and dry-run the bundled offline example:

```powershell
$sample = (Resolve-Path .\flows\samples\ai-jobs-sample.txt).Path.Replace("\", "/")
$env:PHANTOM_FLOW_SAMPLE = "file:///$sample"
$env:PHANTOM_FLOW_STUB_LLM = "1"
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --dry-run --strict --json
```

Run the same example end-to-end with no network and a deterministic LLM stub:

```powershell
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --json --record-out .\artifacts\local-text-summary.run.json
Remove-Item Env:\PHANTOM_FLOW_SAMPLE
Remove-Item Env:\PHANTOM_FLOW_STUB_LLM
```

Public block inputs, outputs, side effects, and failure behavior are documented
in [docs/BLOCK_CONTRACT.md](docs/BLOCK_CONTRACT.md).
The stable run artifact schema written by `--record-out` is documented in
[docs/RUN_ARTIFACT_CONTRACT.md](docs/RUN_ARTIFACT_CONTRACT.md).
Approval-gated side effects and the local state/log store written by
`--state-dir` are documented in
[docs/STATE_AND_APPROVAL_CONTRACT.md](docs/STATE_AND_APPROVAL_CONTRACT.md).

P2 approval/state example:

```powershell
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --dry-run --strict --state-dir .\artifacts\state
```

Steps or outbound actions marked `requires_approval: true` are blocked before
execution unless the run includes `--approve <step-id>`, `--approve <block>`, or
`--approve all`; blocked approval gates exit `3` and can still write
`--record-out` / `--state-dir` artifacts.

P3 local automation scenario proof:

```powershell
python -m phantom_flow.runner scenario .\flows\examples\local-automation-scenario.yaml --out-dir .\artifacts\local-automation-scenario
```

This writes `plan.json`, `blocked.json`, `approved.json`, `state/`,
`scenario.log`, `stdout.log`, and `scenario-summary.json` in the output
directory. The flow runs offline against the bundled sample fixture, blocks the
local report write until approval, then reruns with the discovered approval id. See
[docs/LOCAL_AUTOMATION_SCENARIO.md](docs/LOCAL_AUTOMATION_SCENARIO.md).

📄 完整文件(定位 / 快速上手 / 狀態 / 開源生態與方向):見 [docs/phantom-flow.md](docs/phantom-flow.md)

目前 shipped engine 是 local-first YAML runner；完整現況和未實作項目請看 [ROADMAP.md](ROADMAP.md)，設計邊界請看 [DESIGN.md](DESIGN.md)。

`ai_automation_framework/` 與 `data_analysis/` 是 staged source subtrees，保留作為未來 block adapter 的來源；它們 are not imported by the engine，也不代表那些工具已經是可用的 native blocks。
