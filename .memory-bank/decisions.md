# Decisions

## 2026-07-19 — Read-only scope

The project checks public and private owned repositories. It does not perform deletion, archiving, visibility changes, or any other repository mutation.

## 2026-07-19 — Conservative classification

Only a deeply verified asset-empty repository may become `DELETE_CANDIDATE`. Inactivity, fork status, duplicate naming, or weak public metadata alone produce `MANUAL_REVIEW`.

## 2026-07-19 — Standard-library implementation

Use Python 3.11 standard library only for the runtime. This minimizes dependency and supply-chain complexity.

## 2026-07-19 — Local static review

Generate a self-contained HTML review page with localStorage and JSON export. Do not run a server or make browser-side GitHub requests.
