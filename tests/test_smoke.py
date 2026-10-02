# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""Smoke test: the package imports, and the base install stays light."""

import json
import subprocess
import sys

import saltmarsh

HEAVY = (
    "torch",
    "torchvision",
    "mujoco",
    "gymnasium",
    "lerobot",
    "rerun",
    "open3d",
    "pettingzoo",
    "py_trees",
    "pinocchio",
    "mink",
    "stable_baselines3",
    "jax",
    "rclpy",
)


def test_version_and_parts():
    assert saltmarsh.__version__
    assert saltmarsh.PARTS == (
        "data",
        "perception",
        "movement",
        "behavior",
        "simulation",
        "gaming",
        "eval",
    )


def test_importing_every_part_imports_no_heavy_dependency():
    # A fresh interpreter, so modules imported by pytest or other tests don't count.
    code = (
        "import importlib, json, sys\n"
        "import saltmarsh\n"
        "for part in saltmarsh.PARTS:\n"
        "    importlib.import_module('saltmarsh.' + part)\n"
        "importlib.import_module('saltmarsh.movement.ros')\n"
        f"heavy = {HEAVY!r}\n"
        "print(json.dumps(sorted(m for m in heavy if m in sys.modules)))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], check=True, capture_output=True, text=True
    ).stdout
    assert json.loads(out) == []
