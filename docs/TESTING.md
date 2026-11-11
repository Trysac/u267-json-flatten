# Testing

```sh
pytest tests/test_json_flatten.py
```

## What the tests cover

`tests/test_json_flatten.py` exercises the public API:

- `test_first_example_from_spec` — the acceptance example with root, child-table and scalar-array tables.
- `test_to_csv_and_formatting` — CRLF row terminators, empty fields for `None`, `true`/`false`, floats and `nan`.
- `test_different_keys_share_one_table` — records with different keys share one table and missing values are `None`.
- `test_collision_mixed_array_and_empty` — `column_collision`, `mixed_array`, empty arrays and empty objects.
- `test_array_of_arrays` — nested arrays create the chained child tables `root.m` and `root.m.value`.
- `test_id_field_and_duplicate` — `id_field` behaviour and `duplicate_id`.
- `test_limits` — `too_deep`, `too_many_rows`, `too_many_columns` and `invalid_record`.
- `test_max_depth_applies_to_nested_arrays` — `max_depth` applies to arrays nested inside arrays.

## Adding a test

Write the failing test first, test through the public API rather than private helpers, and add it to `tests/test_json_flatten.py`.
