# Agent instructions

## Repository identity

- Repository: `zh4men9/github-rep-safe-cleaner`
- Purpose: inspect owned public/private GitHub repositories and produce manual cleanup candidates.
- Central collaboration rules: `zh4men9/ai-collaboration-workbench`, GitHub collaboration prompt stable `2.0.3`.

## Absolute safety boundary

This repository must never contain or invoke a capability that:

- deletes a GitHub repository;
- archives or unarchives a GitHub repository;
- changes repository visibility;
- modifies repository settings, files, branches, issues, pull requests, labels, releases, Actions, secrets, or permissions;
- writes to any inspected repository;
- generates an executable deletion script.

The user performs every real GitHub cleanup action manually outside this project.

## Required workflow

1. Read `.memory-bank/LATEST_HANDOFF.md` and `.memory-bank/AUTOMATION_GATE.yaml`.
2. Treat all inspected repositories as read-only data sources.
3. Keep the GitHub transport GET/HEAD-only and endpoint-allowlisted.
4. Run the safety gate and unit tests after changes.
5. Update Memory Bank and the latest handoff before pausing.
6. Never weaken a conservative classification to increase candidate count.
