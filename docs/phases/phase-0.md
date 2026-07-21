# Phase 0 — discovery and design

## Status

Complete.

## Objective and starting state

Inspect the repository, establish permanent engineering rules, select the architecture, identify risks, and define the delivery roadmap. The supplied folder was empty and was not a Git repository, so there was no existing code to preserve or migrate.

## What was delivered

- Root `AGENTS.md` containing permanent architecture, security, tenancy, testing, migration, and evidence rules.
- Modular-monolith architecture decision and Mermaid diagram.
- Initial entity-relationship design and security-risk analysis.
- Six-phase roadmap with Phase 1 acceptance criteria.
- Initial README and repository layout.

## How it works

ResolveHub is one deployable FastAPI application with domain modules and one PostgreSQL source of truth. Module services own business rules; routes remain transport adapters. Redis supplies ephemeral coordination. Temporal and object storage are introduced only in the phases that require them.

## Security decisions

Tenant ownership is explicit through `organisation_id`. Permission strings replace role-name checks. UUIDs are public identifiers, timestamps are UTC, opaque security tokens are stored only as hashes, and every phase must add cross-tenant tests.

## Verification

This was a design phase. The repository state was inspected, the complete supplied project plan was read, and the created documentation was reviewed. No implementation or runtime-success claim was made in this phase.

## Limitations at completion

There was no runnable application, database schema, API, or automated test suite yet.

## Next milestone

Phase 1: application foundation, identity, organisations, permissions, and departments.

