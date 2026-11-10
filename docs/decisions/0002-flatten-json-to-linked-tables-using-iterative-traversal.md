# Flatten JSON to linked tables using iterative traversal

Status: accepted (generated, pending human review)

## Context

Nested JSON records must be converted into a set of relational tables without relying on recursion, which could hit Python's recursion limit before the configured max_depth. The library must handle arrays of objects, scalars, and nested arrays, maintain deterministic column order, and enforce resource limits.

## Decision

Implement flatten with an explicit worklist of value and array tasks, avoiding recursion entirely. Child tables are created on first encounter and named by joining parent table and key path with the separator. Column order is first-seen across records, with missing values filled as None. Identity columns (_id, _parent_id, _index) are prepended deterministically.

## Consequences

The algorithm is iterative and safe for deeply nested input up to max_depth. Child tables are linked by generated parent keys, allowing reconstruction of relationships. Resource limits (max_rows, max_columns, max_depth) are enforced during traversal, raising typed FlattenError. The CSV output follows RFC 4180 with specified formatting rules.
