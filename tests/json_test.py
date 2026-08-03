# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 Scipp contributors (https://github.com/scipp)
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

import chexus
import chexus.json as chexus_json


def _read_json(tmp_path: Path, content: dict[str, Any]) -> chexus.Group:
    path = tmp_path / "template.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return chexus.read_json(str(path))


def _tree_with_dataset(config: dict[str, Any]) -> dict[str, Any]:
    return {"name": "", "children": [{"module": "dataset", "config": config}]}


def _dataset_from_config(tmp_path: Path, config: dict[str, Any]) -> chexus.Dataset:
    root = _read_json(tmp_path, _tree_with_dataset(config))
    node = root.children[config["name"]]
    assert isinstance(node, chexus.Dataset)
    return node


def test_read_json_dataset_stores_values_and_reads_dtype(tmp_path: Path):
    node = _dataset_from_config(
        tmp_path,
        {
            "name": "depends_on",
            "dtype": "string",
            "values": "/entry/instrument/detector/transform",
        },
    )

    assert node.value == "/entry/instrument/detector/transform"
    assert np.dtype(node.dtype) == np.dtype("U")


def test_read_json_dataset_ignores_config_type(tmp_path: Path):
    node = _dataset_from_config(
        tmp_path, {"name": "value", "type": "string", "values": 1}
    )

    assert node.value == 1
    assert np.dtype(node.dtype) == np.dtype(int)


def test_read_json_dataset_does_not_store_large_values(tmp_path: Path, monkeypatch):
    value = [["larger"], [1, 2, 3]]
    monkeypatch.setattr(
        chexus_json,
        "_MAX_STORED_DATASET_VALUE_SIZE",
        sys.getsizeof(value) + 1,
    )
    node = _dataset_from_config(tmp_path, {"name": "value", "values": value})

    assert node.value is chexus_json.dataset_was_too_big
    assert np.dtype(node.dtype) == np.dtype(object)


def test_read_json_dataset_without_dtype_or_values_leaves_dtype_unset(
    tmp_path: Path,
):
    node = _dataset_from_config(tmp_path, {"name": "value"})

    assert node.dtype is None
    assert node.value is None


def test_read_json_ignores_child_without_module_or_type(tmp_path: Path):
    root = _read_json(
        tmp_path,
        {
            "name": "",
            "children": [
                {
                    "config": {
                        "name": "jaw_3_l",
                        "source": "/entry/parameters/jaw_3_l",
                    }
                }
            ],
        },
    )

    assert root.children == {}


def test_read_json_static_depends_on_value_validates_target(tmp_path: Path):
    content = {
        "name": "",
        "children": [
            {
                "name": "detector",
                "type": "group",
                "children": [
                    {
                        "module": "dataset",
                        "config": {
                            "name": "depends_on",
                            "dtype": "string",
                            "values": "/detector/transform",
                        },
                    },
                    {
                        "module": "dataset",
                        "config": {
                            "name": "transform",
                            "dtype": "double",
                            "values": 0.0,
                        },
                        "attributes": [
                            {"name": "transformation_type", "values": "rotation"},
                            {"name": "vector", "values": [0.0, 1.0, 0.0]},
                            {"name": "depends_on", "values": "."},
                        ],
                    },
                ],
            }
        ],
    }
    root = _read_json(tmp_path, content)

    results = chexus.validate(
        root, validators=[chexus.validators.depends_on_target_missing()]
    )

    result = results[chexus.validators.depends_on_target_missing]
    assert result.fails == 0
