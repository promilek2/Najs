# ADR-003: Two package-management layers

- Status: accepted
- Date: 2026-08-31

## Decision

Pacman resolves and installs packages. `najs` owns policy, profiles, snapshots,
history, candidate-root validation, activation, and rollback. Direct pacman use
remains possible but is detected as state drift.

The first implementation exposes only read operations. Mutating commands require
an offline-root pacman adapter, service-start suppression, boot artifact staging,
and integration tests before becoming public.

## Consequences

Najs does not implement a dependency solver or content-addressed package store.
Package script behavior in candidate roots is a core risk and must be tested.
