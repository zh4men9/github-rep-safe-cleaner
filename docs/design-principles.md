# Design principles

- Prefer false negatives over false-positive deletion candidates.
- Separate evidence, classification, and user decision.
- Make missing evidence visible.
- Keep inspected repositories outside every write path.
- Use immutable run artifacts for reproducibility.
- Keep runtime dependencies minimal.
- Require real-account feedback before changing thresholds.
