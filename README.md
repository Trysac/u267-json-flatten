# json-flatten

[![PyPI version](https://img.shields.io/pypi/v/trysac-json-flatten)](https://pypi.org/project/trysac-json-flatten/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-json-flatten)](LICENSE)

Flatten nested JSON records into relational tables: dotted columns for objects, child tables with parent keys for arrays, deterministic column order and RFC 4180 CSV output

## Problem

Nested JSON from APIs and event logs has to land in spreadsheets, SQL tables or dataframes, and simple dot-flattening either explodes arrays into `item.0.sku`, `item.1.sku` columns or drops them. This library splits a list of records into a root table and child tables linked by generated keys, with documented rules for every shape, and exports any table as RFC 4180 CSV.

## Install

```sh
pip install trysac-json-flatten
# or
uv add trysac-json-flatten
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from json_flatten import flatten, to_csv

tables = flatten(
    [{"id": 7, "customer": {"name": "Ana"}, "items": [{"sku": "A", "qty": 2}], "tags": ["x"]}]
)
print(tables["root"].columns)  # ('_id', 'id', 'customer.name')
print(tables["root.items"].rows)  # [(1, 1, 0, 'A', 2)]
print(to_csv(tables["root.tags"]))
```

Command line: read a JSON array (or JSON Lines with `--jsonl`) and write one `<table>.csv` per table into a directory.

```sh
json-flatten data.json --out outdir   # writes outdir/root.csv, outdir/root.items.csv, ...
```

## Public API

- `flatten(records, *, root="root", sep=".", id_field=None, max_depth=32, max_rows=1_000_000, max_columns=1000) -> dict[str, Table]` returns tables in creation order, the root table first.
- `Table(name: str, columns: tuple[str, ...], rows: list[tuple[object, ...]])` is a frozen dataclass; rows follow column order and missing values are `None`.
- `to_csv(table) -> str` uses `csv.writer` with CRLF line endings; `None` is an empty field, booleans are `true`/`false`, floats use `repr`.
- `FlattenError(code)` carries a `code` typed as `column_collision`, `mixed_array`, `duplicate_id`, `too_deep`, `too_many_rows`, `too_many_columns`, `invalid_record` or `invalid_json`; `flatten` raises the first seven, and the CLI reports invalid JSON separately.

Options and limits: arrays of objects, scalars or nested arrays become child tables named `<parent table><sep><key path>`; child rows carry `_id`, `_parent_id` and `_index`; `max_depth` defaults to 32, `max_rows` to 1,000,000 and `max_columns` to 1000; `id_field` uses a scalar record field as the root `_id` and rejects duplicates.

## Why not pandas.json_normalize

`pandas.json_normalize` requires pandas, and arrays are left as Python lists unless a separate `record_path` is used. This library has no runtime dependencies, turns every array into a linked table with `_id`, `_parent_id` and `_index`, and keeps the parent/child relation in the output.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
