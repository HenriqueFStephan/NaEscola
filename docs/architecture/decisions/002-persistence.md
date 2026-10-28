# ADR 002 — File persistence first

## Status

Accepted.

## Decision

Grades, lessons, and generation tasks are JSON documents. IDs are stable strings such as `ef-4-ma-ef04ma09`. The curriculum schema version is `1.0.0`.

Business rules call the catalog and stores, not file paths scattered through route handlers. Replacing a store with MongoDB should not require rewriting validation or the publication gate.

Runtime locks and budgets are written under `data/runtime/`, which is gitignored. Published lessons and curriculum files are versioned.

## Consequences

The repository stays inspectable. Concurrent writers are limited to a file lock per topic. This is not a multi-server lock.
