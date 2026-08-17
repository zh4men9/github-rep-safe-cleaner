# Troubleshooting

## No token found

Authenticate GitHub CLI with `gh auth login`, or set `GH_TOKEN`/`GITHUB_TOKEN` in the shell. Never write the token into a project file.

## Private repositories are missing

The authenticated credential lacks read access to those repositories. Update the credential outside the project and rerun.

## Connection reset / timeout

Version 1.1 retries transient read-only requests with bounded exponential backoff and jitter. Retry messages are printed as `Retry x/5 ...`.

If retries for one probe are exhausted, that repository keeps unknown evidence and is routed to manual review; the scanner continues with the next repository. Remaining probes for that repository are skipped to avoid repeated long waits during an outage.

The scanner writes `checkpoint.json` after each deep-verification target. Rerun with the same `--output` directory to resume successful unchanged targets. Do not remove the output directory before a resume run.

## Deep probe errors

The affected repository is forced away from automatic deletion candidacy. Check the error in `inventory.json`; do not infer emptiness.

## Rate limit is low

Preserve the run artifacts and rerun later. Do not disable safety checks or replace the client with a broad write-capable SDK.
