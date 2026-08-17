# User workflow

1. Run the read-only scan.
2. Open `review.html`.
3. Filter by `DELETE_CANDIDATE`, then inspect each repository link and evidence.
4. Record `KEEP`, `DELETE_MANUALLY`, or `REVIEW_LATER`.
5. Export `decisions.json`.
6. Perform any chosen GitHub action manually in GitHub, outside this project.
7. Run a new scan after manual cleanup to verify the account state.

No decision in the review page triggers a GitHub action.
