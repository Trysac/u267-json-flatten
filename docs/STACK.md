# Stack

## Runtime

- Python >= 3.10.
- Standard library only: `argparse`, `collections.abc`, `csv`, `dataclasses`, `io`, `json`, `logging`, `os`, `sys`, `typing`.
- No runtime dependencies.

## Development

- `pytest` for the test suite in `tests/test_json_flatten.py`.
- `py.typed` ships with the package for PEP 561 type information.
- Source uses `from __future__ import annotations` and full type annotations.

## Considered and discarded

- **pandas / `json_normalize`** — a heavy dependency, and arrays are left as Python lists instead of becoming linked tables, which loses the parent/child relation.
- **`flatten_json`** (PyPI) — dependency-based, and array elements become `item.0.sku` columns.
- **Recursive flattening** — deep input would hit the interpreter recursion limit before `max_depth`; the implementation uses an explicit stack instead.
- **SQL DDL generation / type inference** — out of scope; CSV is the only export.
