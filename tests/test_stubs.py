# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""The optional parts fail with a clear message, never a bare ImportError deep inside."""

import importlib.util

import pytest

from saltmarsh._extras import MissingExtraError
from saltmarsh.gaming import arena_available, make_arena_env
from saltmarsh.movement import ros


def test_arena_is_not_published_yet():
    assert not arena_available()
    with pytest.raises(MissingExtraError, match="not published yet"):
        make_arena_env()


@pytest.mark.skipif(ros.rclpy_available(), reason="ROS 2 is installed here")
def test_ros_bridge_explains_rclpy():
    with pytest.raises(MissingExtraError, match="not on PyPI"):
        ros.rclpy()


@pytest.mark.parametrize(
    ("module", "func"),
    [
        ("torch", "saltmarsh.behavior:torch"),
        ("open3d", "saltmarsh.perception:open3d"),
        ("py_trees", "saltmarsh.gaming:py_trees"),
    ],
)
def test_missing_extra_names_the_extra(module, func):
    if importlib.util.find_spec(module) is not None:
        pytest.skip(f"{module} is installed")
    mod_name, attr = func.split(":")
    fn = getattr(importlib.import_module(mod_name), attr)
    with pytest.raises(MissingExtraError, match=r"saltmarsh\["):
        fn()
