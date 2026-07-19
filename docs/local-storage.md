# Local decision storage

The review page stores decisions in browser localStorage under an owner-specific key. Clearing browser data removes those decisions. Export `decisions.json` when a durable local record is needed. This storage never synchronizes with GitHub.
