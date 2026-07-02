# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Scipp contributors (https://github.com/scipp)
import json
import sys
from typing import Any

import numpy as np

from .tree import Dataset, Group

_MAX_STORED_DATASET_VALUE_SIZE = 100 * 1024


class _DatasetWasTooBig:
    def __repr__(self) -> str:
        return "dataset_was_too_big"


dataset_was_too_big = _DatasetWasTooBig()


def read_json(path: str) -> Group:
    """
    Read JSON NeXus file and return tree of datasets and groups.

    The JSON looks something like this:

    {
        "name": "delay",
        "type": "group",
        "attributes": [
            {
                "name": "NX_class",
                "dtype": "string",
                "values": "NXlog"
            }
        ],
        "children": [
            {
                "module": "f142",
                "config": {
                    "source": "source",
                    "topic": "topic",
                    "dtype": "double",
                    "value_units": "ns"
                },
                "attributes": [
                    {
                        "name": "units",
                        "dtype": "string",
                        "values": "ns"
                    }
                ]
            },
            {
                "module": "dataset",
                "config": {
                    "name": "slits",
                    "values": 1,
                    "dtype": "int64"
                }
            },
        ]
    },
    """
    with open(path) as f:
        return _read_group(json.load(f))


def _read_group(group: dict[str, Any], parent: Group | None = None) -> Group:
    """Read JSON group"""
    name = group.get("name", '')
    if parent is not None:
        name = parent.name + '/' + name
    grp = Group(name=name, attrs={}, children={}, parent=parent)
    for child in group["children"]:
        if not isinstance(child, dict):
            continue
        module = child.get("module")
        if module is None and "type" in child:
            if child["type"] == "group":
                grp.children[child["name"]] = _read_group(child, parent=grp)
        elif module == "dataset":
            grp.children[child["config"]["name"]] = _read_dataset(child, parent=grp)
        elif module in ["f142", 'f144']:
            grp.children[child["config"]["source"]] = _read_source(child, parent=grp)
        else:
            pass
    grp.attrs = _read_attrs(group)
    return grp


def _read_dataset(dataset: dict[str, Any], parent: Group) -> Dataset:
    """Read JSON dataset"""
    config = dataset["config"]
    name = parent.name + '/' + config["name"]
    if "dtype" in config:
        dtype = _translate_dtype(config["dtype"])
    elif "values" in config:
        dtype = np.dtype(type(config["values"]))
    else:
        dtype = None

    kwargs = {}
    if "values" in config:
        if _json_value_fits(config["values"], _MAX_STORED_DATASET_VALUE_SIZE):
            kwargs["value"] = config["values"]
        else:
            kwargs["value"] = dataset_was_too_big

    return Dataset(
        name=name,
        shape=None,
        dtype=dtype,
        attrs=_read_attrs(dataset),
        parent=parent,
        **kwargs,
    )


def _json_value_fits(value: Any, limit: int) -> bool:
    if (size := _fast_json_value_size(value, limit)) is not None:
        return size < limit
    return sys.getsizeof(json.dumps(value)) < limit


def _fast_json_value_size(value: Any, limit: int) -> int | None:
    if value is None or isinstance(value, str | int | float | bool):
        return sys.getsizeof(value)
    if not isinstance(value, list):
        return None
    size = sys.getsizeof(value)
    for item in value:
        if size >= limit:
            break
        if (item_size := _fast_json_value_size(item, limit - size)) is None:
            return None
        size += item_size
    return size


def _read_source(source: dict[str, Any], parent: Group) -> Dataset:
    """Read JSON source"""
    name = parent.name + '/' + source['config']["source"]
    ds = Dataset(
        name=name,
        shape=None,
        dtype=_translate_dtype(source["config"]["dtype"]),
        attrs=_read_attrs(source),
        parent=parent,
    )
    if (units := source["config"].get("value_units")) is not None:
        ds.attrs['units'] = units
    return ds


def _translate_dtype(dtype: str) -> str:
    """Translate dtype from JSON to Python/NumPy"""
    if dtype == "double":
        return np.float64
    if dtype == "float":
        return np.float32
    if dtype == "string":
        return np.dtype('U')
    return np.dtype(dtype)


def _read_attrs(node: dict[str, Any]) -> dict[str, Any]:
    """Read JSON attributes"""
    attrs = {}
    for attr in node.get("attributes", {}):
        attrs[attr["name"]] = attr["values"]
    return attrs
