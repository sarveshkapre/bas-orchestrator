# Schema Export

Use the CLI to export JSON schemas for campaign and evidence packs.

```bash
bas export-schemas --out schemas
```

Outputs:
- `schemas/campaign.schema.json`
- `schemas/evidence.schema.json`
- `schemas/summary.schema.json`

The summary schema aligns with `bas report --json` output.
