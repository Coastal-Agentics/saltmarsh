# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
import copy
import math
import tomllib
from pathlib import Path

import pytest

from saltmarsh.eval import LimitsError, load_limits
from saltmarsh.eval.limits import parse_limits

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "limits" / "example-arm.toml"


@pytest.fixture
def doc():
    with EXAMPLE.open("rb") as fh:
        return tomllib.load(fh)


def test_example_loads():
    limits = load_limits(EXAMPLE)
    assert limits.robot == "example-arm"
    assert set(limits.joints) == {"shoulder", "elbow", "wrist"}
    assert limits.joints["elbow"].position == (-2.0, 2.0)


def test_violations():
    limits = load_limits(EXAMPLE)
    assert limits.violations(joint_position={"shoulder": 0.0}, ee_speed=0.1) == []
    found = limits.violations(
        joint_position={"shoulder": 2.0, "knee": 0.0},
        joint_velocity={"elbow": -1.6},
        joint_torque={"wrist": math.nan},
        ee_position=[0.0, 0.0, 0.5],
        ee_speed=0.3,
        contact_force=11.0,
    )
    assert len(found) == 7


def mutate(doc, path, value):
    doc = copy.deepcopy(doc)
    node = doc
    for key in path[:-1]:
        node = node[key]
    if value is KeyError:
        del node[path[-1]]
    else:
        node[path[-1]] = value
    return doc


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("schema_version",), 2),
        (("robot",), ""),
        (("joints",), {}),
        (("joints", "elbow", "position"), [1.0, -1.0]),
        (("joints", "elbow", "position"), [0.0]),
        (("joints", "elbow", "velocity"), 0),
        (("joints", "elbow", "torque"), -1.0),
        (("joints", "elbow", "torque"), "3"),
        (("joints", "elbow", "torque"), KeyError),
        (("joints", "elbow", "damping"), 1.0),
        (("workspace", "min"), [0.5, -0.3, 0.0]),
        (("end_effector", "max_speed"), math.inf),
        (("end_effector",), KeyError),
        (("extra_section",), {}),
    ],
)
def test_invalid_files_are_refused(doc, path, value):
    with pytest.raises(LimitsError):
        parse_limits(mutate(doc, path, value))


def test_missing_and_malformed_files(tmp_path):
    with pytest.raises(LimitsError, match="not found"):
        load_limits(tmp_path / "nope.toml")
    bad = tmp_path / "bad.toml"
    bad.write_text("robot = ")
    with pytest.raises(LimitsError, match="invalid TOML"):
        load_limits(bad)
