# Scout Agent

## Role
Continuous intelligence scout. Monitors data sources (patents, scientific publications, industry news) and produces raw signals.

## Inputs
- `domain`: string (e.g. "lkm")
- `source_id`: optional UUID (if scoped to one source)
- `war_room`: bool (if true, shorter lookback, higher priority)

## Outputs
Array of `RawSignal` objects:
- `title`, `summary`, `url`, `source_type`
- `relevance_score` (0–1)
- `relevance_rationale`

## Tools
- `web_search` — Anthropic native web search tool
- `web_fetch` — httpx-based URL fetcher

## Parameters (defaults)
- Model: `claude-sonnet-4-6`
- Temperature: 0.3
- Max tokens: 8192

## Notes
- Does NOT assess margin, feasibility, or compliance
- Filters out signals with relevance_score < 0.4
- Runs every 6 hours for LKM domain (cron: `0 */6 * * *`)
- War Room mode: runs every 7 days lookback instead of 30
