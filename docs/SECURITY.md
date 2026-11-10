# Security

## Reporting

See [`SECURITY.md`](../SECURITY.md) at the repository root for supported versions and the private reporting channel.

## Threat model

`json-flatten` is a standard-library library: `flatten` and `to_csv` perform no network, filesystem or process access, and the library does not parse JSON itself (callers pass already-decoded mappings). The CLI reads one local file and, with `--out`, writes CSV files into the directory named on the command line.

The main risks are resource exhaustion from hostile input and unsafe output handling:

| Risk | Defended by |
|---|---|
| Pathologically deep nesting | `max_depth` (default 32); traversal uses explicit stacks and does not recurse. |
| Huge inputs | `max_rows` (default 1,000,000) and `max_columns` (default 1000). |
| Huge files through the CLI | Inputs above 104,857,600 bytes are rejected with `input_too_large`, exit 2. |
| Invalid records | A non-mapping record raises `FlattenError` with code `invalid_record` naming its index. |
| Invalid CLI JSON | Invalid JSON or a non-array JSON document returns exit 2. |

Not defended:

- CSV injection in spreadsheets: `to_csv` writes cells verbatim using RFC 4180 quoting; sanitise before opening untrusted CSV in a spreadsheet.
- Output filenames: the CLI writes `<table>.csv` using table names derived from `--root`, the separator and input keys; table names are not sanitised as path components.
- Memory use per value: `max_rows` bounds row count, not the size of individual strings or objects; `flatten` materialises all tables and rows.

## Gates

The package has no runtime dependencies, so there is no dependency-audit surface. Changes should be reviewed for the limit checks above and for the CLI filename construction.
