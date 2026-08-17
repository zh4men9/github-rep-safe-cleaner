# Version history

## 1.1.0 — 2026-08-17

Reliability release driven by the first real-account test. Adds bounded retry with exponential backoff and jitter for transient read failures, converts exhausted per-repository transport failures into explicit unknown evidence instead of aborting the whole scan, skips redundant remaining probes after a transport exhaustion, and persists fingerprinted deep-verification checkpoints for resume.

## 1.0.0 — 2026-07-19

Complete read-only workflow: account scan, conservative classification, immutable reports, local review page, decision export, tests, CI, and Memory Bank.

## 0.5.0 — 2026-07-19

Added public/private owned-repository inventory, candidate-targeted deep read-only probes, duplicate grouping, and conservative classification.

## 0.1.0 — 2026-07-19

Established GET/HEAD-only transport, endpoint allowlist, no-mutation project rules, safety tests, and read-only CI permissions.
