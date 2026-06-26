# Block Contract

This file defines the public contract for the blocks that ship in the
installable `phantom_flow` package. The staged source subtrees are not shipped
native blocks.

## Public Demo Path

Validate and lint a bundled offline flow without network or filesystem writes:

```powershell
$sample = (Resolve-Path .\flows\samples\ai-jobs-sample.txt).Path.Replace("\", "/")
$env:PHANTOM_FLOW_SAMPLE = "file:///$sample"
$env:PHANTOM_FLOW_STUB_LLM = "1"
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --dry-run --strict --json
```

Run the same flow end-to-end with the deterministic LLM stub:

```powershell
python -m phantom_flow.runner .\flows\examples\local-text-summary.yaml --validate --json --record-out .\artifacts\local-text-summary.run.json
Remove-Item Env:\PHANTOM_FLOW_SAMPLE
Remove-Item Env:\PHANTOM_FLOW_STUB_LLM
```

`--dry-run` plans only. It must not fetch network content or perform block
filesystem side effects; `--record-out` is the explicit user-requested
exception that writes only the run artifact.
`PHANTOM_FLOW_STUB_LLM=1` keeps the LLM step deterministic and offline.
`--record-out` writes the stable run artifact documented in
`docs/RUN_ARTIFACT_CONTRACT.md`.

## Shipped Blocks

| Block | Input | Output | Side effects | Failure behavior |
| --- | --- | --- | --- | --- |
| `tools.http_get` | `url`, optional `timeout`, `max_bytes`, `user_agent` | `url`, `status`, `body`, `body_len` | Performs bounded read from `http(s)://` or `file://` only when not in dry-run | Raises from `urllib` on unavailable URLs; callers record step failure |
| `tools.youtube_transcript` | YouTube `url`, optional `languages`, `cache_file` | `text`, `text_len`, `source`, `video_id`, `error` | Optional live transcript fetch; can fall back to checked-in cached text | Raises if live fetch fails and no cache is usable |
| `pipeline.regex_count` | `input`, `pattern` | `value`, `pattern` | None | Invalid regex raises during execution |
| `pipeline.filter` | `input`, `keywords` | `matched`, `matched_count`, `passes` | None | Returns no matches for empty input |
| `pipeline.llm_summarize` | `input`, optional `prompt`, `force_stub`, `timeout`, `model_hint` | `summary`, `backend`, `error` | May call phantom/LLM unless stubbed; timeout is bounded | Falls back through the LLM driver where configured and reports backend/error |
| `pipeline.if` | `condition` | `true`, `false`, `condition` | None | Unsupported or malformed comparisons evaluate false |
| `pipeline.subprocess` | `cmd`, optional `timeout` | `stdout`, `stderr`, `returncode`, `timed_out` | Runs a bounded local subprocess when not in dry-run | Missing commands, OS errors, and timeouts return structured non-zero results |
| `actions.log_append` | `path`, `line` | `path`, `appended` | Appends one line to a local file and creates parent directories | Filesystem errors raise and are recorded as action failure |
| `actions.stdout` | `line` | `line` | Writes one line to stdout | Standard stream errors propagate |

## Open-Source Safety Rules

- Public examples must use bundled samples, `file://`, or explicitly public URLs.
- Secrets must come from environment variables and must not appear in flow files.
- External network blocks and subprocess blocks must stay bounded by timeouts and
  documented as side-effecting.
- Dry-run and strict validation are the first public support path for new flows.
