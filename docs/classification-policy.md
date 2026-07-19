# Classification policy

## DELETE_CANDIDATE

Requires a completed deep read-only probe with no commits, branches, releases, issues, pull requests, or probe errors.

## MANUAL_REVIEW

Used for incomplete evidence, API errors, duplicate-name groups, low-signal forks, archived repositories, long inactivity, and weak public metadata.

## KEEP

No deletion-grade evidence was found.

The policy optimizes against false-positive deletion candidates. It does not optimize for producing a large candidate list.
