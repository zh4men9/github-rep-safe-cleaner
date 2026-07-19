# Safety model

## Threat model

The principal failure is not a bad score. It is an automated or accidental mutation of a GitHub repository while the system is supposed to be auditing it.

The project therefore assumes that prompts, future agents, configuration errors, copied code, and user-interface mistakes can all occur. Safety cannot depend only on a warning in the README.

## Structural controls

### Read-only transport

`ReadOnlyGitHubClient` accepts only `GET` and `HEAD`. Any other method raises `SafetyViolation` before a network request is created.

### Endpoint allowlist

The client accepts only:

- authenticated-user metadata;
- owned repository listing;
- repository metadata;
- commits, releases, issues, pull requests, and branches listing.

Unknown endpoints are rejected even when they could be read-only. New endpoints require an explicit code change and tests.

### No mutation module

There is no service, command, adapter, interface, or optional flag for repository deletion, archiving, visibility changes, or settings mutation.

### Conservative evidence flow

A repository becomes `DELETE_CANDIDATE` only when deep verification succeeds and proves all checked asset categories are empty. Missing evidence or API errors force `MANUAL_REVIEW`.

### Local review page

`review.html` embeds scan data and contains no network client. It stores decisions locally and exports a JSON file. A decision labelled `DELETE_MANUALLY` is a note for the user, not an executable command.

### CI permissions

GitHub Actions declares only:

```yaml
permissions:
  contents: read
```

CI validates code and demo artifacts but cannot mutate repositories.

## Non-goals

- automatic cleanup;
- bulk repository operations;
- automatic archiving;
- automatic visibility management;
- automatic issue or pull-request changes;
- scheduling unattended GitHub actions;
- inferring deletion from inactivity alone.
