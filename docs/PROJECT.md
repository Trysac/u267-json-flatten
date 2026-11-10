# Project record

## What this is

`trysac-json-flatten` (import name `json_flatten`) flattens nested JSON records into relational tables: dotted columns for objects, child tables with parent keys for arrays, deterministic column order and RFC 4180 CSV output. MIT licensed, Python >= 3.10, no runtime dependencies.

## Why

Nested JSON from APIs and event logs has to land in spreadsheets, SQL tables or dataframes. Simple dot-flattening either explodes arrays into `item.0.sku`, `item.1.sku` columns or drops them. Re-writing the normalisation for each payload is tedious and inconsistent, so the library fixes the rules once: every array becomes a linked table and generated keys keep the relations.

## Scope

In scope: objects to dotted columns, arrays to child tables (`_id`, `_parent_id`, `_index`), arrays of arrays, CSV export, a small CLI, deterministic column order, and explicit limits for depth, rows and columns.

Out of scope: unflattening, type inference beyond JSON types, SQL DDL generation, streaming output for inputs larger than memory.

## Status

0.1.0 — the public API (`flatten`, `to_csv`, `Table`, `FlattenError`) and the CLI are implemented and covered by `tests/test_json_flatten.py`.

## Factory run u267 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1673 | 25499 | 0 | 3200 | 0.0517 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 15893 | 9058 | 0 | 251648 | 0.0086 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 5794 | 751 | 0 | 18688 | 0.0014 |
| 2026-11-10 | audit | deepseek-flash | no | 23996 | 28302 | 0 | 354304 | 0.0216 |
| 2026-11-10 | fix-3 | deepseek-flash | no | 18320 | 10203 | 0 | 446080 | 0.0102 |
| 2026-11-10 | docs | deepseek-flash | no | 109379 | 8470 | 0 | 256 | 0.0215 |

Total: $0.1150. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
