"""Tests for json_flatten."""

import json

import pytest

from json_flatten import FlattenError, Table, flatten, to_csv
from json_flatten.__main__ import main

FIRST_EXAMPLE = [
    {
        "id": 7,
        "customer": {"name": "Ana"},
        "items": [{"sku": "A", "qty": 2}, {"sku": "B", "qty": 1}],
        "tags": ["x", "y"],
    }
]


def test_first_example_from_spec():
    tables = flatten(FIRST_EXAMPLE)
    assert list(tables.keys()) == ["root", "root.items", "root.tags"]

    root = tables["root"]
    assert root.name == "root"
    assert root.columns == ("_id", "id", "customer.name")
    assert root.rows == [(1, 7, "Ana")]

    items = tables["root.items"]
    assert items.columns == ("_id", "_parent_id", "_index", "sku", "qty")
    assert items.rows == [(1, 1, 0, "A", 2), (2, 1, 1, "B", 1)]

    tags = tables["root.tags"]
    assert tags.columns == ("_id", "_parent_id", "_index", "value")
    assert tags.rows == [(1, 1, 0, "x"), (2, 1, 1, "y")]


def test_to_csv_and_formatting():
    tables = flatten(FIRST_EXAMPLE)
    tags = tables["root.tags"]
    csv_text = to_csv(tags)
    assert csv_text == "_id,_parent_id,_index,value\r\n1,1,0,x\r\n2,1,1,y\r\n"

    table = Table(
        name="t",
        columns=("_id", "a", "b", "c", "d", "e", "f"),
        rows=[(1, None, True, False, 1.5, float("nan"), "x")],
    )
    csv_text = to_csv(table)
    assert csv_text == "_id,a,b,c,d,e,f\r\n1,,true,false,1.5,nan,x\r\n"


def test_different_keys_share_one_table():
    tables = flatten([{"a": 1}, {"b": 2}])
    root = tables["root"]
    assert root.columns == ("_id", "a", "b")
    assert root.rows == [(1, 1, None), (2, None, 2)]


def test_collision_mixed_array_and_empty():
    with pytest.raises(FlattenError) as exc_info:
        flatten([{"a.b": 1, "a": {"b": 2}}])
    assert exc_info.value.code == "column_collision"
    assert "a.b" in str(exc_info.value)

    with pytest.raises(FlattenError) as exc_info:
        flatten([{"arr": [1, {}]}])
    assert exc_info.value.code == "mixed_array"

    tables = flatten([{"empty_obj": {}, "empty_arr": []}])
    root = tables["root"]
    assert root.columns == ("_id",)
    assert root.rows == [(1,)]
    assert "root.empty_arr" not in tables


def test_array_of_arrays():
    tables = flatten([{"m": [[1, 2]]}])
    assert list(tables.keys()) == ["root", "root.m", "root.m.value"]

    root = tables["root"]
    assert root.columns == ("_id",)
    assert root.rows == [(1,)]

    outer = tables["root.m"]
    assert outer.columns == ("_id", "_parent_id", "_index")
    assert outer.rows == [(1, 1, 0)]

    inner = tables["root.m.value"]
    assert inner.columns == ("_id", "_parent_id", "_index", "value")
    assert inner.rows == [(1, 1, 0, 1), (2, 1, 1, 2)]


def test_id_field_and_duplicate():
    records = [{"id": "a", "name": "A"}, {"id": "b", "name": "B"}]
    tables = flatten(records, id_field="id")
    root = tables["root"]
    assert root.columns == ("_id", "name")
    assert [(row[0], row[1]) for row in root.rows] == [("a", "A"), ("b", "B")]

    records_with_child = [{"id": "a", "items": [{"x": 1}]}]
    tables = flatten(records_with_child, id_field="id")
    items = tables["root.items"]
    assert items.rows[0][1] == "a"  # _parent_id

    with pytest.raises(FlattenError) as exc_info:
        flatten([{"id": "a"}, {"id": "a"}], id_field="id")
    assert exc_info.value.code == "duplicate_id"


def test_limits():
    with pytest.raises(FlattenError) as exc_info:
        flatten([{"a": {"b": 1}}], max_depth=0)
    assert exc_info.value.code == "too_deep"

    with pytest.raises(FlattenError) as exc_info:
        flatten([{"a": 1}, {"a": 2}], max_rows=1)
    assert exc_info.value.code == "too_many_rows"

    with pytest.raises(FlattenError) as exc_info:
        flatten([{"a": 1, "b": 2}], max_columns=2)
    assert exc_info.value.code == "too_many_columns"

    with pytest.raises(FlattenError) as exc_info:
        flatten([1])
    assert exc_info.value.code == "invalid_record"
    assert "index 0" in str(exc_info.value)


def test_max_depth_applies_to_nested_arrays():
    with pytest.raises(FlattenError) as exc_info:
        flatten([{"m": [[[1]]]}], max_depth=2)
    assert exc_info.value.code == "too_deep"

    # Exactly at the limit still works: one array of arrays inside the root record.
    tables = flatten([{"m": [[1]]}], max_depth=2)
    assert tables["root.m.value"].rows == [(1, 1, 0, 1)]


def test_id_field_validation():
    with pytest.raises(FlattenError) as exc_info:
        flatten([{"id": {"k": 1}}], id_field="id")
    assert exc_info.value.code == "invalid_record"
    assert "index 0" in str(exc_info.value)

    with pytest.raises(FlattenError) as exc_info:
        flatten([{"id": [1]}], id_field="id")
    assert exc_info.value.code == "invalid_record"

    with pytest.raises(FlattenError) as exc_info:
        flatten([{"name": "no id"}], id_field="id")
    assert exc_info.value.code == "invalid_record"
    assert "missing id field" in str(exc_info.value)

    # ``True`` and ``1`` are different ids even though they compare equal.
    tables = flatten([{"id": True}, {"id": 1}], id_field="id")
    assert [row[0] for row in tables["root"].rows] == [True, 1]


def test_edge_cases():
    tables = flatten([{"a.b": 1, "a": {"c": 2}}])
    root = tables["root"]
    assert root.columns == ("_id", "a.b", "a.c")
    assert root.rows == [(1, 1, 2)]

    tables = flatten([{"名前": "太郎", "nested": {"数据": 1}}])
    root = tables["root"]
    assert root.columns == ("_id", "名前", "nested.数据")
    assert root.rows == [(1, "太郎", 1)]

    tables = flatten([{"a": {"b": 1}, "arr": [{"x": 2}]}], sep="__")
    assert "root__arr" in tables
    assert tables["root"].columns == ("_id", "a__b")


def test_main_writes_csv(tmp_path):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(FIRST_EXAMPLE))
    out_dir = tmp_path / "out"
    ret = main([str(data_file), "--out", str(out_dir)])
    assert ret == 0

    assert (out_dir / "root.csv").exists()
    assert (out_dir / "root.items.csv").exists()
    assert (out_dir / "root.tags.csv").exists()

    with open(out_dir / "root.csv", encoding="utf-8", newline="") as f:
        root_csv = f.read()
    assert root_csv == "_id,id,customer.name\r\n1,7,Ana\r\n"


def test_main_acceptance_outdir(tmp_path, monkeypatch):
    data_file = tmp_path / "data.json"
    data_file.write_text(json.dumps(FIRST_EXAMPLE))
    monkeypatch.chdir(tmp_path)
    ret = main(["data.json", "--out", "outdir"])
    assert ret == 0

    out_dir = tmp_path / "outdir"
    assert (out_dir / "root.csv").exists()
    assert (out_dir / "root.items.csv").exists()
    assert (out_dir / "root.tags.csv").exists()


def test_main_invalid_inputs(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{bad")
    ret = main([str(bad_file)])
    assert ret == 2

    large_file = tmp_path / "large.json"
    with open(large_file, "wb") as f:
        f.truncate(104_857_601)
    ret = main([str(large_file)])
    assert ret == 2


def test_main_jsonl(tmp_path):
    jsonl_file = tmp_path / "data.jsonl"
    jsonl_file.write_text('{"a": 1}\n{"b": 2}\n')
    ret = main([str(jsonl_file), "--jsonl"])
    assert ret == 0  # no --out prints to stdout, exit 0
