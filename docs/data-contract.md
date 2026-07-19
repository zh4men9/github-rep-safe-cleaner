# Data contract

`inventory.json` is the canonical run output.

Top-level fields:

- `schema_version`
- `generated_at`
- `owner`
- `safety`
- `summary`
- `rate_limit`
- `assessments`

Each assessment contains the normalized repository record, category, confidence, priority, reasons, counter-evidence, and optional duplicate group. Missing or failed deep evidence must remain explicit and cannot be converted into deletion confidence.
