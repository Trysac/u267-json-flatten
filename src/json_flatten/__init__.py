"""Flatten nested JSON records into relational tables.

The module provides :func:`flatten`, :func:`to_csv`, :class:`Table`, and
:class:`FlattenError`.
"""

from __future__ import annotations

import csv
import io
import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal, cast

__all__ = ["FlattenError", "Table", "__version__", "flatten", "to_csv"]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

FlattenErrorCode = Literal[
    "column_collision",
    "mixed_array",
    "duplicate_id",
    "too_deep",
    "too_many_rows",
    "too_many_columns",
    "invalid_record",
    "invalid_json",
]


class FlattenError(Exception):
    """Error raised while flattening records."""

    def __init__(self, code: FlattenErrorCode, message: str = "") -> None:
        self.code = code
        super().__init__(message or code)


@dataclass(frozen=True)
class Table:
    """A relational table produced by :func:`flatten`."""

    name: str
    columns: tuple[str, ...]
    rows: list[tuple[object, ...]]


@dataclass
class _RowDraft:
    id: object
    parent_id: object | None
    index: int | None
    data: dict[str, object] = field(default_factory=dict)


@dataclass
class _TableAccumulator:
    name: str
    is_root: bool
    data_columns: list[str] = field(default_factory=list)
    rows: list[_RowDraft] = field(default_factory=list)
    next_child_id: int = 1


def flatten(
    records: Iterable[Mapping[str, object]],
    *,
    root: str = "root",
    sep: str = ".",
    id_field: str | None = None,
    max_depth: int = 32,
    max_rows: int = 1_000_000,
    max_columns: int = 1000,
) -> dict[str, Table]:
    """Flatten an iterable of mappings into a dictionary of tables.

    The root table is named ``root`` (or ``root`` replaced by the *root*
    argument).  Arrays of objects, scalars, or nested arrays become child
    tables whose names are derived by joining table and key names with
    *sep*.  The first table returned is the root table; subsequent tables
    appear in creation order.

    Raises:
        FlattenError: with a ``code`` describing the failure.
    """
    tables: dict[str, _TableAccumulator] = {}
    tables_order: list[_TableAccumulator] = []
    root_acc = _TableAccumulator(name=root, is_root=True)
    tables[root] = root_acc
    tables_order.append(root_acc)

    global_row_count = 0
    root_auto_id = 1
    seen_root_ids: set[tuple[type, object]] = set()

    value_stack: list[
        tuple[object, _TableAccumulator, object, int | None, int, str, dict[str, object]]
    ] = []
    array_stack: list[tuple[list[object], _TableAccumulator, object, int | None, int, str]] = []

    def add_row(
        acc: _TableAccumulator,
        id_: object,
        parent_id: object | None,
        index: int | None,
    ) -> _RowDraft:
        nonlocal global_row_count
        global_row_count += 1
        if global_row_count > max_rows:
            raise FlattenError("too_many_rows")
        row = _RowDraft(id=id_, parent_id=parent_id, index=index)
        acc.rows.append(row)
        return row

    def get_or_create_table(name: str, is_root: bool) -> _TableAccumulator:
        if name not in tables:
            acc = _TableAccumulator(name=name, is_root=is_root)
            tables[name] = acc
            tables_order.append(acc)
        return tables[name]

    def handle_array(
        arr: list[object],
        parent_table: _TableAccumulator,
        parent_row_id: object,
        parent_index: int | None,
        depth: int,
        path: str,
    ) -> None:
        if not arr:
            return
        if depth >= max_depth:
            raise FlattenError("too_deep")
        first = arr[0]
        if isinstance(first, Mapping):
            category = "object"
        elif isinstance(first, list):
            category = "array"
        else:
            category = "scalar"
        for item in arr:
            if isinstance(item, Mapping) and category != "object":
                raise FlattenError("mixed_array")
            if isinstance(item, list) and category != "array":
                raise FlattenError("mixed_array")
            if not isinstance(item, (Mapping, list)) and category != "scalar":
                raise FlattenError("mixed_array")

        child_table_name = f"{parent_table.name}{sep}{path}"
        child_acc = get_or_create_table(child_table_name, is_root=False)

        if category == "scalar":
            data_col = "value"
            base_cols = 3
            if data_col not in child_acc.data_columns:
                if base_cols + len(child_acc.data_columns) + 1 > max_columns:
                    raise FlattenError("too_many_columns")
                child_acc.data_columns.append(data_col)
            for idx, scalar in enumerate(arr):
                child_row = add_row(child_acc, child_acc.next_child_id, parent_row_id, idx)
                child_acc.next_child_id += 1
                child_row.data[data_col] = scalar
            return

        pending: list[tuple[object, int, _RowDraft]] = []
        for idx, item in enumerate(arr):
            child_row = add_row(child_acc, child_acc.next_child_id, parent_row_id, idx)
            child_acc.next_child_id += 1
            pending.append((item, idx, child_row))

        # Push in reverse so the explicit stack processes the first element first.
        for item, idx, child_row in reversed(pending):
            if category == "object":
                # handle_array validated every element above.
                obj = cast("Mapping[str, object]", item)
                for key, value in reversed(list(obj.items())):
                    value_stack.append(
                        (
                            value,
                            child_acc,
                            child_row.id,
                            idx,
                            depth + 1,
                            key,
                            child_row.data,
                        )
                    )
            else:  # category == "array"
                # handle_array validated every element above.
                nested = cast("list[object]", item)
                array_stack.append((nested, child_acc, child_row.id, idx, depth + 1, "value"))

    for record_index, record in enumerate(records):
        if not isinstance(record, Mapping):
            msg = f"record at index {record_index}: expected mapping"
            raise FlattenError("invalid_record", msg)

        if id_field is None:
            root_id: object = root_auto_id
            root_auto_id += 1
        else:
            if id_field not in record:
                msg = f"record at index {record_index}: missing id field {id_field!r}"
                raise FlattenError("invalid_record", msg)
            root_id = record[id_field]
            if isinstance(root_id, (Mapping, list)):
                msg = f"record at index {record_index}: id field {id_field!r} must be a scalar"
                raise FlattenError("invalid_record", msg)
            # Tag the id with its type so ``True`` and ``1`` do not collide.
            id_key = (type(root_id), root_id)
            if id_key in seen_root_ids:
                msg = f"duplicate id: {root_id!r}"
                raise FlattenError("duplicate_id", msg)
            seen_root_ids.add(id_key)

        root_row = add_row(root_acc, root_id, None, None)

        value_stack.clear()
        array_stack.clear()
        record_items = [
            (key, value) for key, value in record.items() if id_field is None or key != id_field
        ]
        # Push in reverse so the explicit stack processes keys in first-seen order.
        for key, value in reversed(record_items):
            value_stack.append((value, root_acc, root_id, None, 0, key, root_row.data))

        while value_stack or array_stack:
            if value_stack:
                value, table, parent_row_id, parent_idx, depth, path, row_data = value_stack.pop()
                if isinstance(value, Mapping):
                    if depth >= max_depth:
                        raise FlattenError("too_deep")
                    for k, v in reversed(list(value.items())):
                        child_path = f"{path}{sep}{k}" if path else k
                        value_stack.append(
                            (
                                v,
                                table,
                                parent_row_id,
                                parent_idx,
                                depth + 1,
                                child_path,
                                row_data,
                            )
                        )
                elif isinstance(value, list):
                    if depth >= max_depth:
                        raise FlattenError("too_deep")
                    handle_array(value, table, parent_row_id, parent_idx, depth, path)
                else:
                    if path in row_data:
                        raise FlattenError("column_collision", f"column collision: {path!r}")
                    base_cols = 1 if table.is_root else 3
                    if path not in table.data_columns:
                        if base_cols + len(table.data_columns) + 1 > max_columns:
                            raise FlattenError("too_many_columns")
                        table.data_columns.append(path)
                    row_data[path] = value
            else:
                arr, table, parent_row_id, parent_idx, depth, path = array_stack.pop()
                handle_array(arr, table, parent_row_id, parent_idx, depth, path)

    result: dict[str, Table] = {}
    for acc in tables_order:
        columns: list[str] = []
        if acc.is_root:
            columns.append("_id")
        else:
            columns.extend(["_id", "_parent_id", "_index"])
        columns.extend(acc.data_columns)

        rows: list[tuple[object, ...]] = []
        for row in acc.rows:
            data_values = tuple(row.data.get(c) for c in acc.data_columns)
            if acc.is_root:
                rows.append((row.id, *data_values))
            else:
                rows.append((row.id, row.parent_id, row.index, *data_values))
        result[acc.name] = Table(name=acc.name, columns=tuple(columns), rows=rows)

    return result


def _csv_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(value)
    return str(value)


def to_csv(table: Table) -> str:
    """Return an RFC 4180 CSV representation of *table*.

    Rows are terminated by ``\\r\\n``.  ``None`` is written as an empty
    field, booleans as ``true``/``false``, floats via ``repr``, and all
    other values via ``str``.
    """
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(table.columns)
    for row in table.rows:
        writer.writerow(_csv_cell(value) for value in row)
    return output.getvalue()
