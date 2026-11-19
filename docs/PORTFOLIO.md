# Discussing Taylor Catalog Lab in an interview

## CV description

**Taylor Catalog Lab — music data application.** Modernized a Python coursework project into a FastAPI/SQLite service with compressed radix-tree title search, a collision-safe resizable hash table, album analytics and standardized audio-feature similarity. Added a public catalog API integration, browser dashboard, Docker packaging and regression tests.

## Engineering discussion

- Show how radix edge splitting handles shared prefixes and duplicate titles. Tests compare its output with a simple linear scan on randomized strings.
- Explain why the old probing approach could stall and how resizing plus bounded load prevents saturation.
- Explain how standardization prevents tempo from overwhelming features whose values lie between zero and one.
- Distinguish the original historical CSV's audio features from iTunes metadata, which has no such features.
- Discuss transactional batch validation, stable external identifiers and idempotent upserts.

## What was verified

Six pytest cases cover randomized radix behavior, forced hash collisions, invalid-batch atomicity, API integration and missing-feature handling. The original 476-row CSV was imported locally without publishing it. A live iTunes lookup imported 192 public metadata records during validation. These counts are observations from that run, not a guarantee that the external catalog will stay unchanged.

GitHub Actions runs the tests and builds the container. This is content-based nearest-neighbor similarity, not a trained personalization model. The public offline fixture contains fictional titles and synthetic features.
