# Known limitations

- The scanner evaluates repositories owned by the authenticated user; organization-owned repositories are out of scope.
- Duplicate detection is name-based and intentionally routes to manual review.
- Forks are not automatically proven redundant; they remain manual review unless independently verified empty.
- GitHub API rate limits depend on authentication and repository count.
- The local review page does not synchronize decisions across browsers or devices.
- A real authenticated account scan is required to validate candidate quality.
