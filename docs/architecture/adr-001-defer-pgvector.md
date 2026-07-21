# ADR 001 — defer semantic vectors until they are justified

## Status

Accepted on 2026-07-17.

## Context

Phase 4 requires standard PostgreSQL search to work before semantic similarity is considered. A useful pgvector design also requires a real embedding model, documented dimensions, versioning, re-embedding behavior, an index strategy, and a representative evaluation dataset. ResolveHub currently has only a deterministic local AI provider, deliberately has no paid model dependency, and has no evidence that fake vectors would improve duplicate detection.

## Decision

Do not enable pgvector or persist meaningless deterministic embeddings in Phase 4. Use PostgreSQL full-text search to produce tenant-scoped duplicate candidates and pass those candidates through the replaceable suggestion provider. Revisit pgvector only after a real embedding provider and reproducible relevance evaluation exist.

## Consequences

- Local development and automated tests require no model downloads, paid API, or additional PostgreSQL image.
- Duplicate suggestions remain lexical and may miss semantically similar wording.
- Any later vector migration must document model name, dimensions, distance metric, index type, tenant filtering, re-embedding, privacy, and measured relevance before adoption.
