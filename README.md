# json-flatten

[![PyPI version](https://img.shields.io/pypi/v/trysac-json-flatten)](https://pypi.org/project/trysac-json-flatten/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-json-flatten)](LICENSE)
[![CI](https://github.com/Trysac/u267-json-flatten/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u267-json-flatten/actions/workflows/ci.yml)

Flatten nested JSON records into relational tables: dotted columns for objects, child tables with parent keys for arrays, deterministic column order and RFC 4180 CSV output

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-json-flatten
# or
uv add trysac-json-flatten
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import json_flatten

# normalize() trims surrounding whitespace and lower-cases the text.
print(json_flatten.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    json_flatten.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
