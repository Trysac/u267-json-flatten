# 0001 — Arrays become linked child tables

## Status

Accepted (0.1.0).

## Context

The input is a list of nested JSON records. Two common approaches exist:

1. Dot-flatten everything, including array indices: `items.0.sku`, `items.1.sku`. The column set
   depends on the largest array seen, empty slots become `None`, and the parent/child relation is
   implicit in key names.
2. Keep arrays as opaque values (`json_normalize` without `record_path`). The data is not usable
   in a relational target and the relation to the parent row is lost.

Both make downstream SQL, spreadsheet and dataframe loads inconsistent between payloads.

## Decision

Every array becomes its own table named `<parent table><sep><key path>`. Rows of that table carry
`_id` (1-based, per table), `_parent_id` (the parent row's `_id`) and `_index` (0-based position in
the array). An array of scalars gets one column named `value`; an array of arrays adds rows to the
child table and pushes the element's items into `<child table><sep>value`. Arrays that mix objects,
scalars or arrays raise `FlattenError("mixed_array")` instead of guessing.

With `id_field`, root rows use that record field as `_id` so child rows point at business ids
rather than generated ones.

## Consequences

- Tables are many-to-one related and can be joined on `_parent_id = _id`.
- Column order is deterministic: `_id`, `_parent_id`, `_index`, then data columns in first-seen
  order across records.
- Mixed arrays are rejected; callers must normalise before flattening.
- Unflattening (rebuilding the nested document) is out of scope.
