# Troubleshooting

## No token found

Authenticate GitHub CLI with `gh auth login`, or set `GH_TOKEN`/`GITHUB_TOKEN` in the shell. Never write the token into a project file.

## Private repositories are missing

The authenticated credential lacks read access to those repositories. Update the credential outside the project and rerun.

## Deep probe errors

The affected repository is forced to `MANUAL_REVIEW`. Check the error in `inventory.json`; do not infer emptiness.

## Rate limit is low

Preserve the run artifacts and rerun later. Do not disable safety checks or replace the client with a broad write-capable SDK.
