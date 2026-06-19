# phantom-flow

[![CI](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-flow/actions/workflows/ci.yml)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)

> 極小、local-first、mesh-native 的 YAML 工作流執行器（phantom-mesh 生態系）。近乎純標準函式庫(唯一硬相依 PyYAML)；LLM 步驟可經 phantom-mesh 路由,缺 CLI 則退回決定性 stub。

📄 完整文件(定位 / 快速上手 / 狀態 / 開源生態與方向):見 [docs/phantom-flow.md](docs/phantom-flow.md)

目前 shipped engine 是 local-first YAML runner；完整現況和未實作項目請看 [ROADMAP.md](ROADMAP.md)，設計邊界請看 [DESIGN.md](DESIGN.md)。

`ai_automation_framework/` 與 `data_analysis/` 是 staged source subtrees，保留作為未來 block adapter 的來源；它們 are not imported by the engine，也不代表那些工具已經是可用的 native blocks。
