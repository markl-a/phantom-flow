> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-flow.md;此為歷史版本。

# phantom-flow — 開源生態與方向

> 領域掃描：**workflow automation／event-driven／cron+webhook 編排**。
> 目的：將 phantom-flow 定位於現有主流方案之中，以便我們採用／包裝／參考
> 正確的對象，而*不要*重新打造 n8n。每一項外部數據都有來源依據並標註時間戳；
> 彼此衝突或無法重新查證的數字皆標記為 `[unverified]`。
>
> _編纂於 2026-06-19。Star 數每日浮動——請視為數量級，而非精確值。_
> 狀態 SSOT 仍以 [`../ROADMAP.md`](../ROADMAP.md) 為準；
> 本文件談的是**方向**，而非狀態。

---

## 1. phantom-flow 現況（有依據的盤點）

今日**已在 `main` 上交付且具測試覆蓋**的內容（依據 `ROADMAP.md` + git log）：

- 一個小型的 **local-first YAML 工作流執行器**——`phantom_flow/`（約 750 行，
  近乎純標準函式庫，唯一硬性相依為 PyYAML）。不是伺服器、不是 UI、不是 SaaS。
- **YAML 載入器 + `${...}` 替換**（`step.field`、`date.today`、
  `date.now`、`env.X`）。
- **9 個原生區塊**：`tools.http_get`（含 `file://`）、
  `tools.youtube_transcript`、`pipeline.regex_count`、`pipeline.filter`、
  `pipeline.if`、`pipeline.llm_summarize`、`pipeline.subprocess`、
  `actions.log_append`、`actions.stdout`。
- **CLI**：`--dry-run`、`--strict`（registry lint）、`--validate`（schema）、
  `--json`。Schema 驗證 + 結構化 `RunRecord`。
- **LLM 步驟透過 `phantom exec` 路由**（即 phantom-mesh CLI），並具備
  決定性的 stub 後備；降級原因會被顯示出來。這就是
  mesh-native 的接點。
- **HTTP webhook listener**——`phantom-flow serve <flow>`（標準函式庫 `http.server`，
  不用 fastapi/uvicorn）；對 `trigger.url` 發出 POST 會植入 `ctx["event"]` 並驅動
  `run_flow`。Commit `f9de0d5`、`b9f3315`。
- **Cron 排程器（單次、hermetic）**——`schedule_matches(expr, dt)`
  純標準函式庫的 5 欄位匹配器（`*`、清單、範圍、`*/n`；不用 croniter）；
  `phantom-flow schedule <flow> --once [--now ISO]`。Commit `ad4c12d`、`7975a36`。
- **Hermetic pytest 測試套件 + GitHub Actions CI**；隨附完全離線的範例
  flows。

**誠實地說尚未打造**（依據 ROADMAP「Planned-next」）：event-driven 的 mesh 觸發器
（`trigger.type=event` 僅驗證形狀）、cluster-aware dispatch、daemon 式的
sleep-loop 排程器、視覺化編輯器、市集，以及對 vendored 的
`ai_automation_framework/` + `data_analysis/` 子樹的任何接線（已備源碼，**尚未
import**）。

**一句話定位：** phantom-flow 是一個*微型、受治理、mesh-native* 的 flow
執行器——與下方那些 10 萬行的視覺化平台處於光譜的兩個極端。它的差異化**不在於**
整合數量；而在於 local-first、近乎純標準函式庫，並經由 phantom-mesh governor 路由。

---

## 2. 生態全景

### 2.1 視覺化／no-code 自動化平台（「n8n 級別」）

這些是 phantom-flow 最常被*拿來比較*、也最容易被要求去「追趕」的專案。它們是
龐大的多年期團隊。

| 專案 | URL | Stars | 語言 | 授權 | 成熟度 | 對單人、local-first、mesh-native 利基的契合度／落差 |
|---|---|---|---|---|---|---|
| **n8n** | github.com/n8n-io/n8n | ~193k `[unverified]`（live repo 頁面 2026-06-19；彙整型 blog 仍引用 ~60–70k——落差極大，請勿引用精確數字） | TypeScript | Sustainable Use License（fair-code，**非 OSI**） | 非常成熟，400+ 整合 | 業界主流。可自架但需 Node.js + fair-code（商用受限）。**對我們的落差：** 笨重、未受治理、不具 mesh 意識。**不要重建。** 參考其 block/trigger UX；可選擇透過 webhook 互通。 |
| **Activepieces** | github.com/activepieces/activepieces | ~23k | TypeScript | MIT（+ 部分 EE） | 成熟，~280+ pieces，AI/MCP 取向 | 寬鬆授權、MCP 前瞻。最「友善」的主流方案。**參考** 其 piece 模型；不值得克隆。 |
| **Node-RED** | github.com/node-red/node-red | ~21k `[unverified]` | JavaScript | Apache-2.0 | 非常成熟（OpenJS Foundation），IoT/event 取向 | 真正 event-driven + flow-based + 道地開源。在*哲學*上最接近的近親（小型 runtime、接線式區塊）。**重點參考** 其 flow/event 模型。 |
| **Huginn** | github.com/huginn/huginn | ~42k `[unverified]` | Ruby | MIT | 成熟，web 監測／agent-event | 用於個人自動化／爬取的 agent-and-event 模型——與我們是同一類*使用者*（一個人、自己的機器）。Ruby/Rails 技術棧是落差所在。**參考** 其 agent-emits-event 模式。 |
| **Dify** | github.com/langgenius/dify | ~60k+ `[unverified]` | Python/TS | Modified Apache-2.0 | 成熟，LLM-app + agentic workflow | LLM-app 平台，伺服器 + UI 偏重。在「pipeline 中的 LLM 步驟」上有重疊，但它是產品而非函式庫。**僅供參考。** |
| **Flowise** | github.com/FlowiseAI/Flowise | ~30k+ `[unverified]` | TypeScript | Apache-2.0 | 成熟，視覺化 LLM/agent 建構器 | 視覺化拖拉式 LLM 鏈。若哪天想做視覺化編輯器，動工前先**參考**。 |

### 2.2 開發者優先／程式碼編排

| 專案 | URL | Stars | 語言 | 授權 | 成熟度 | 契合度／落差 |
|---|---|---|---|---|---|---|
| **Windmill** | github.com/windmill-labs/windmill | ~16.8k | Rust（+ TS） | AGPL-3.0（EE 功能為專有） | 成熟 | 從 script 到 workflow，搭配 Git + 自動產生的 UI；**Rust 核心** 與 phantom-mesh 相同。AGPL 與 phantom-mesh 的 AGPL 世界對齊。不過伺服器偏重。**參考** 其 hermetic-script + 版本控管模型；可能有長尾互通空間。 |
| **Trigger.dev** | github.com/triggerdotdev/trigger.dev | ~13.6k | TypeScript | Apache-2.0 | 成熟 | 以 TS 實作的耐久長時任務（retries/queues/observability）。解決我們明確*延後*的「長任務在重啟後存活」問題。若我們將來需要，**參考** 其 durable-task 語意。 |
| **Temporal** | github.com/temporalio/temporal | ~16.4k `[unverified]` | Go | MIT | 非常成熟，企業級 | 耐久執行（durable-execution）引擎。笨重（伺服器 + workers + 自有 SDK）。對單人本地工具而言**嚴重過度設計**。僅**參考** 其概念（durable execution）。 |

### 2.3 資料管線編排器（相鄰領域，但**非我們的賽道**）

列在此處是為了刻意不踏進這條賽道——這些是 DAG/ETL 工具，原始 spec 早已宣告
**不做**（「不取代 Apache Airflow」）。

| 專案 | URL | Stars | 語言 | 授權 | 備註 |
|---|---|---|---|---|---|
| **Apache Airflow** | github.com/apache/airflow | very large `[unverified]` | Python | Apache-2.0 | DAG/ETL 排程器。不同問題（資料管線，而非個別工作流）。 |
| **Dagster** | github.com/dagster-io/dagster | large `[unverified]` | Python | Apache-2.0 | 以 asset 為中心的資料編排。相鄰，但非我們的使用者。 |
| **Prefect** | github.com/PrefectHQ/prefect | large `[unverified]` | Python | Apache-2.0 | Python 原生的管線編排。相鄰，但非我們的使用者。 |

### 2.4 AI-agent 工作流建構器（在「LLM 區塊」上重疊）

| 專案 | URL | Stars | 語言 | 授權 | 契合度／落差 |
|---|---|---|---|---|---|
| **LangGraph** | github.com/langchain-ai/langgraph | ~90k+ `[unverified]` | Python | MIT | 以圖為基礎的 agent runtime（routing、human-in-loop、checkpoints）。是函式庫，而非 workflow 產品。**參考** 其「human-in-loop checkpoint」模式——它直接對應到 phantom-mesh 的 governor + 手機核可。 |

---

## 3. 建議方向

**判定標籤：** `BUILD`（自己做，這是利基）· `WRAP`（包裝在現有事物之上的轉接層）·
`REFERENCE`（借用其概念／UX，不要依賴）·
`AVOID`（不在賽道內）。

### 3.1 真正屬於我們、該 BUILD 的（護城河）

護城河**不是**「又一個 workflow 引擎」。而是 §2 中沒有人佔據的那個*交集*：

> **受治理、local-first、mesh-native 的 flows**——一個微型執行器，其中每一個副作用
> （subprocess、HTTP、對外動作）都能經由 phantom-mesh 的
> **governor + flight-recorder + 手機核可**路由，跑在你自己擁有的機器上，
> 且小到一個人就能稽核整體。

具體而言，`BUILD`：

1. **Governor 把關的區塊**——來自 phantom-mesh apex 的 `④ safe-unattended`
   差異化點。mesh-native 的 flows，其風險步驟會暫停以待手機 approve/deny。
   *§2 中沒有任何專案具備此能力。* 這是單一最高價值、最具防禦性的東西。
2. **`trigger.type=event` 對接真實 mesh 事件**——下一個尚未打造的觸發器；
   補齊 cron + webhook + event 三件套。便宜、本地、高度契合。
3. **維持近乎純標準函式庫 + hermetic。** 小巧的體積*本身就是*一項特性
   （可稽核性、不陷入相依地獄）。把「加了一個沉重相依」視為退步。

### 3.2 該 WRAP 而非自己寫的

4. **Vendored 子樹工具**（`ai_automation_framework/`、`data_analysis/`）——
   各自於需要時 `WRAP`，藏在一個薄薄的 `fn(spec, ctx)` 轉接區塊之後。不要
   批次 import。在每個工具都包裝 + 測試完成前，不要宣稱「30+ 工具」。（這已經是
   DESIGN §4 的決定——此處重申為正確的 OSS 姿態。）
5. **LLM 步驟**已經 `WRAP` 了 phantom-mesh（`phantom exec`）。把它保留為
   *唯一*的 LLM 路徑；不要 vendor LangChain/Dify 式的技術棧。

### 3.3 該 REFERENCE 的（複製其 UX/語意，拒絕其相依）

- **Node-RED / Huginn**——*flow-of-blocks* 與 *agent-emits-event* 模型。
  在精神上最接近；兩者皆道地開源。
- **Activepieces**——「piece」（具型別的轉接器）形狀，待我們將
  block-author 契約形式化時可用。
- **LangGraph**——human-in-loop checkpoint 模式 → 對應到我們的 governor。
- **Trigger.dev / Temporal**——durable-execution *語意*，僅在某個 flow
  確實需要在執行途中存活過重啟時才採用。現在不需要。

### 3.4 該 AVOID 的

- **重建 n8n／視覺化編輯器／市集。** 多年期團隊、400+
  整合、fair-code 商業模式。我們無法、也不應該與此匹敵。
  互通（接受來自 n8n 的 webhook；讓 n8n 呼叫我們的 `serve`）勝過克隆。
- **DAG/ETL 資料管線賽道**（Airflow/Dagster/Prefect）。明確**非**我們的
  使用者（個別工作流，而非資料管線）。
- **常駐伺服器／多租戶 SaaS。** 違反 local-first。

---

## 4. 分階段路徑

依單人多機開發模式排序：**便宜 + 高價值 + 護城河優先**，
外部整合／需操作者決策者殿後。

| 階段 | 目標 | 具體項目（2–4 項） | 判定 |
|---|---|---|---|
| **P1 — 鎖住護城河** | 讓 flows *受治理* | (a) 將 `pipeline.subprocess` + `tools.http_get` + 對外動作路由經過 phantom-mesh governor 閘門；(b) flight-recorder 執行記錄；(c) 高風險步驟的手機 approve/deny | `BUILD` |
| **P2 — 補齊觸發三件套** | cron ✅ + webhook ✅ + **event** | (a) `trigger.type=event` 消費真實 mesh 事件；(b) 撰寫 cron/webhook/event 矩陣文件 | `BUILD` |
| **P3 — 按需包裝** | 把已備源碼轉成真實區塊 | (a) 包裝 2–3 個最受需求的 `ai_automation_framework` 工具為轉接區塊（各自測試）；(b) 或許 1 個 `data_analysis` 區塊 | `WRAP` |
| **P4 — 觸達（受操作者把關）** | 少數幾個真實的對外動作 | (a) email + 一個聊天通道（Telegram/LINE，重用 phantom-mesh 的 notifier）；(b) **僅在真實 flow 需要時** | `WRAP`/`BUILD` |
| **P5 — 互通，而非克隆**（可選／需求 `[unverified]`） | 與生態圈和睦相處 | (a) 接受來自 n8n/Activepieces 的 inbound webhook；(b) 撰寫如何從它們呼叫 phantom-flow `serve` 的文件 | `REFERENCE`／互通 |

視覺化編輯器、市集、cluster-dispatch、durable-execution：**擱置**，直到出現
具體的個人需求 + 操作者決策。不在關鍵路徑上。

---

## 5. 誠實的過度打造警告

- **別重建 n8n。** 它的價值是 400+ 整合，以及由有資金的團隊歷時多年打造的
  精緻編輯器。要匹敵那個是多年期、多人的專案。我們的價值正好*相反*：
  小巧、受治理、本地、可稽核。
- **別把 10 萬行 vendored 程式碼批次接線**來灌水工具數量。每個被包裝的工具
  都是維護 + 授權清查的負債。按需包裝，由真實 flow 驅動。
- **別過早加上伺服器/daemon/UI。** `serve` + `schedule --once` +
  一個外部觸發器（launchd/systemd/phantom-mesh）已經涵蓋真實的
  cron+webhook 需求，毋須長期運行的 daemon。daemon 迴圈在 ROADMAP 中已明確、
  誠實地延後——在需要之前都保持原狀。
- **別追逐 durable execution（Temporal/Trigger.dev）。** 那解決的問題
  （大規模下長任務在崩潰後存活）我們身為單人本地工具並不存在。
  僅在真實 flow 有此需求時才採用其*語意*。
- **別漂移進資料管線賽道。** Airflow/Dagster/Prefect 擁有 ETL；
  我們擁有個別、受治理的個人工作流。不同的使用者。
- **守住相依介面。** 「只有 PyYAML」是一項特性。一個加入沉重 runtime
  相依的 PR 必須對著可稽核性護城河自我辯護。

---

## 來源

- n8n — https://github.com/n8n-io/n8n （授權/定位），
  https://github.com/n8n-io/n8n/blob/master/LICENSE.md
- Activepieces — https://github.com/activepieces/activepieces
- Node-RED — https://github.com/node-red/node-red
- Huginn — https://github.com/huginn/huginn ；
  https://automationatlas.io/tools/huginn/
- Windmill — https://github.com/windmill-labs/windmill ；
  https://www.windmill.dev/blog/airflow-alternatives
- Trigger.dev — https://github.com/triggerdotdev/trigger.dev
- Temporal — https://github.com/temporalio/temporal
- Airflow / Dagster / Prefect 比較 —
  https://www.bytebase.com/blog/top-open-source-workflow-orchestration-tools/ ；
  https://www.pracdata.io/p/state-of-workflow-orchestration-ecosystem-2025
- Dify — https://github.com/langgenius/dify
- Flowise — https://flowiseai.com/ ； https://github.com/FlowiseAI/Flowise
- LangGraph — https://github.com/langchain-ai/langgraph
- 跨工具比較 —
  https://openalternative.co/alternatives/zapier ；
  https://www.booleanbeyond.com/en/insights/n8n-vs-activepieces-vs-windmill-open-source-automation ；
  https://latenode.com/blog/platform-comparisons-alternatives/n8n-alternatives/n8n-alternatives-2025-12-open-source-self-hosted-workflow-automation-tools-compared

> 標記為 `[unverified]` 的數字取自彙整型文章或單次的 live 頁面讀取，未經交叉確認；
> 其中 n8n 的 star 數在不同來源間呈現極大落差，不應被精確引用。
