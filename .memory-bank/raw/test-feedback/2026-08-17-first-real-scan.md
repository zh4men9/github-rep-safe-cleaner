# First real-account scan feedback — 2026-08-17

User ran the v1.0 acceptance script twice on macOS.

Verified before the failure:

- editable install succeeded;
- safety gate passed;
- all 7 existing unit tests passed;
- offline demo artifacts generated;
- GitHub authentication resolved as `zh4men9`;
- 228 owned repositories were loaded, including the authenticated account's public/private scope;
- 94 repositories were selected for deep read-only verification.

Failure 1:

- deep verification reached `13/94` (`zh4men9/awesome-serverless`);
- process terminated with `<urlopen error [Errno 54] Connection reset by peer>`.

Failure 2:

- after rerunning from the beginning, deep verification terminated at `2/94` (`zh4men9/agent-runner-lab`);
- same `<urlopen error [Errno 54] Connection reset by peer>` failure.

Conclusion: transient transport errors are not contained by the current GitHub API error boundary, so a single network reset aborts the entire scan. The next implementation must retry bounded transient failures, convert exhausted per-probe failures into explicit evidence errors, and persist successful probe checkpoints for resume.
