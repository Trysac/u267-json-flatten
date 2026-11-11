# Architecture

`json-flatten` has one job: turn an iterable of JSON-like mappings into a dictionary of flat, relational tables. The package is standard library only.

## Module layout

| Path | Responsibility |
|---|---|
| `src/json_flatten/__init__.py` | Public API: `flatten`, `to_csv`, `Table`, `FlattenError`. |
| `src/json_flatten/__main__.py` | CLI (`json-flatten`): read JSON or JSON Lines, write CSV, enforce the input-size limit. |
| `src/json_flatten/py.typed` | PEP 561 marker; the package ships its types. |
| `tests/test_json_flatten.py` | pytest tests exercising the public API and CLI entry point. |

## Public API

- `Table(name, columns, rows)` — frozen dataclass; `rows` is a list of tuples in column order.
- `flatten(records, *, root="root", sep=".", id_field=None, max_depth=32, max_rows=1_000_000, max_columns=1000) -> dict[str, Table]` — tables in creation order, the root table first.
- `to_csv(table) -> str` — `csv.writer` with CRLF line endings; `None` becomes an empty field, booleans become `true`/`false`, floats use `repr`.
- `FlattenError(code)` — `code` is one of `column_collision`, `mixed_array`, `duplicate_id`, `too_deep`, `too_many_rows`, `too_many_columns`, `invalid_record`, `invalid_json`.

## Flattening algorithm

Records are visited in order. Each record becomes one root row; nested objects become dotted columns (`customer.name`), arrays become child tables named `<parent table><sep><key path>`.

Child rows carry `_id` (1-based per table, or the record's `id_field` value for the root), `_parent_id` (the parent row's `_id`) and `_index` (0-based position in the array). An array of scalars gets a single `value` column; an array of arrays creates one row in the child table and pushes the nested elements into `<child table><sep>value`. Arrays that mix objects, scalars or arrays raise `mixed_array`.

The traversal uses an explicit stack (`value_stack` for values, `array_stack` for deferred array elements) instead of recursion, so deep input never hits the interpreter recursion limit before `max_depth` does. `max_depth`, `max_rows` and `max_columns` are checked on every step.

Column order is `_id` (plus `_parent_id` and `_index` for child tables) followed by data columns in first-seen order across records (depth-first, key order of each object). Missing values are `None`.

## Decisions

Design choices recorded by the implementation: iterative traversal rather than recursion; every array becomes a linked table rather than expanded columns; no runtime dependencies; CSV is the only export.
