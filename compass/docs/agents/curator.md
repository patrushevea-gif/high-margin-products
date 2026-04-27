# Curator Agent

## Role
Deduplicates and clusters raw signals, then forms structured hypothesis drafts.

## Inputs
- `signals`: list of raw signals from Scout
- `domain`: string

## Outputs
```json
{
  "hypotheses": [...],
  "deduplicated_count": 5,
  "clusters_found": 3
}
```

## Parameters (defaults)
- Model: `claude-sonnet-4-6`
- Temperature: 0.4
- Max tokens: 4096

## Notes
- Only creates hypotheses from clusters with relevance_score > 0.6
- Quality over quantity — a bad hypothesis is worse than no hypothesis
- New hypotheses are saved to DB with status `signal_processed`
