# Active context

## Current stage

Version 1.1.0 reliability work is implemented on `agent/read-only-repo-auditor` after the first real-account test exposed transient network-reset failure.

## Main contradiction

The v1.0 pipeline successfully authenticated, loaded 228 owned repositories, and selected 94 deep-verification targets, but an uncaught connection reset aborted the scan twice. The code now contains retries, transport failure containment, and resumable checkpoints; these changes require a second real-account run to prove the failure is resolved in the user's actual network.

## Current route

Keep Draft PR #1 open. Require repository-side CI to pass for the v1.1 head, then rerun the same real scan output path without deleting it. Do not add any GitHub mutation feature.
