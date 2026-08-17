# Decisions

## 2026-07-19 — Read-only scope

The project checks public and private owned repositories. It does not perform deletion, archiving, visibility changes, or any other repository mutation.

## 2026-07-19 — Conservative classification

Only a deeply verified asset-empty repository may become `DELETE_CANDIDATE`. Inactivity, fork status, duplicate naming, or weak public metadata alone produce `MANUAL_REVIEW`.

## 2026-07-19 — Standard-library implementation

Use Python 3.11 standard library only for the runtime. This minimizes dependency and supply-chain complexity.

## 2026-07-19 — Local static review

Generate a self-contained HTML review page with localStorage and JSON export. Do not run a server or make browser-side GitHub requests.

## 2026-08-17 — Retry transient reads inside the read-only transport

`URLError`, `HTTPException`, `OSError`, invalid JSON, HTTP 429, and selected 5xx responses receive bounded retries. This belongs in the transport layer so callers cannot accidentally bypass it.

## 2026-08-17 — Exhausted transport failure is unknown evidence

A per-repository transport failure that survives all retries does not abort the scan and cannot support deletion. Remaining probes for that repository are skipped, its evidence remains unknown, and classification becomes manual review.

## 2026-08-17 — Fingerprinted checkpoint resume

Successful deep-probe results are persisted with repository ID, `updated_at`, and `pushed_at`. A later run reuses them only when the fingerprint still matches; failed or changed repositories are probed again.
