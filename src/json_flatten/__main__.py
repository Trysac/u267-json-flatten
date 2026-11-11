"""Command line interface for json_flatten."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import FlattenError, flatten, to_csv

INPUT_SIZE_LIMIT = 104_857_600


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Command line arguments; if ``None``, ``sys.argv[1:]`` is used.

    Returns:
        Exit code: 0 for success, 2 for usage, IO, or invalid input.
    """
    parser = argparse.ArgumentParser(prog="json_flatten")
    parser.add_argument("input", help="JSON file (array or JSON Lines)")
    parser.add_argument("--out", help="Output directory for CSV files")
    parser.add_argument("--root", default="root", help="Root table name (default: root)")
    parser.add_argument("--sep", default=".", help="Separator for dotted names (default: .)")
    parser.add_argument("--jsonl", action="store_true", help="Input is newline-delimited JSON")

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return int(e.code) if e.code is not None else 2

    input_path = args.input
    try:
        size = os.path.getsize(input_path)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if size > INPUT_SIZE_LIMIT:
        print("input_too_large", file=sys.stderr)
        return 2

    try:
        with open(input_path, encoding="utf-8") as f:
            text = f.read()
        if args.jsonl:
            records: list[dict[str, object]] = []
            for line_no, line in enumerate(text.splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError as exc:
                    print(f"invalid json on line {line_no}: {exc}", file=sys.stderr)
                    return 2
                if not isinstance(rec, dict):
                    print(
                        f"invalid record on line {line_no}: expected object",
                        file=sys.stderr,
                    )
                    return 2
                records.append(rec)
        else:
            data = json.loads(text)
            if not isinstance(data, list):
                print("input must be a JSON array", file=sys.stderr)
                return 2
            records = data
    except json.JSONDecodeError as exc:
        print(f"invalid json: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error reading: {exc}", file=sys.stderr)
        return 2

    try:
        tables = flatten(records, root=args.root, sep=args.sep)
    except FlattenError as exc:
        print(f"error: {exc.code}: {exc}", file=sys.stderr)
        return 2

    if args.out:
        try:
            os.makedirs(args.out, exist_ok=True)
            for name, table in tables.items():
                csv_content = to_csv(table)
                out_path = os.path.join(args.out, f"{name}.csv")
                with open(out_path, "w", encoding="utf-8", newline="") as f:
                    f.write(csv_content)
        except OSError as exc:
            print(f"error writing: {exc}", file=sys.stderr)
            return 2
    else:
        for name, table in tables.items():
            print(f"# {name}")
            print(to_csv(table), end="")

    return 0
