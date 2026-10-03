# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""Per-robot limits files.

Each robot ships a TOML limits file: joint position, velocity and torque
limits, a workspace box, an end-effector speed cap and a contact force cap.
`load_limits` validates the file strictly and refuses anything unexpected.
See `examples/limits/example-arm.toml`.
"""

import math
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


class LimitsError(ValueError):
    """Raised when a limits file is missing, malformed or inconsistent."""


@dataclass(frozen=True)
class JointLimits:
    position: tuple[float, float]
    velocity: float
    torque: float


@dataclass(frozen=True)
class RobotLimits:
    robot: str
    joints: Mapping[str, JointLimits]
    workspace_min: tuple[float, float, float]
    workspace_max: tuple[float, float, float]
    max_ee_speed: float
    max_contact_force: float

    def violations(
        self,
        *,
        joint_position: Mapping[str, float] | None = None,
        joint_velocity: Mapping[str, float] | None = None,
        joint_torque: Mapping[str, float] | None = None,
        ee_position: Sequence[float] | None = None,
        ee_speed: float | None = None,
        contact_force: float | None = None,
    ) -> list[str]:
        """Return a list of human-readable violations; empty means within limits.

        Unknown joint names and non-finite values count as violations.
        """
        out: list[str] = []

        def bad(value: float) -> bool:
            return not math.isfinite(value)

        for name, value in (joint_position or {}).items():
            lim = self.joints.get(name)
            if lim is None:
                out.append(f"unknown joint {name!r}")
            elif bad(value) or not lim.position[0] <= value <= lim.position[1]:
                out.append(f"{name} position {value} outside {lim.position}")
        for kind, values in (("velocity", joint_velocity), ("torque", joint_torque)):
            for name, value in (values or {}).items():
                lim = self.joints.get(name)
                if lim is None:
                    out.append(f"unknown joint {name!r}")
                    continue
                cap = getattr(lim, kind)
                if bad(value) or abs(value) > cap:
                    out.append(f"{name} {kind} {value} exceeds {cap}")
        if ee_position is not None:
            if len(ee_position) != 3:
                out.append("end-effector position must have 3 values")
            else:
                for axis, v, lo, hi in zip(
                    "xyz", ee_position, self.workspace_min, self.workspace_max, strict=True
                ):
                    if bad(v) or not lo <= v <= hi:
                        out.append(f"end-effector {axis}={v} outside workspace [{lo}, {hi}]")
        if ee_speed is not None and (bad(ee_speed) or ee_speed > self.max_ee_speed):
            out.append(f"end-effector speed {ee_speed} exceeds {self.max_ee_speed}")
        if contact_force is not None and (
            bad(contact_force) or contact_force > self.max_contact_force
        ):
            out.append(f"contact force {contact_force} exceeds {self.max_contact_force}")
        return out


def _number(value: Any, where: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise LimitsError(f"{where}: expected a number, got {value!r}")
    value = float(value)
    if not math.isfinite(value):
        raise LimitsError(f"{where}: must be finite")
    if positive and value <= 0:
        raise LimitsError(f"{where}: must be > 0")
    return value


def _keys(table: Any, where: str, required: set[str]) -> Mapping[str, Any]:
    if not isinstance(table, dict):
        raise LimitsError(f"{where}: expected a table")
    missing = required - table.keys()
    extra = table.keys() - required
    if missing:
        raise LimitsError(f"{where}: missing {sorted(missing)}")
    if extra:
        raise LimitsError(f"{where}: unknown keys {sorted(extra)}")
    return table


def _vec(value: Any, where: str, n: int) -> tuple[float, ...]:
    if not isinstance(value, list) or len(value) != n:
        raise LimitsError(f"{where}: expected a list of {n} numbers")
    return tuple(_number(v, f"{where}[{i}]") for i, v in enumerate(value))


def parse_limits(data: Mapping[str, Any]) -> RobotLimits:
    """Validate a parsed limits document and build RobotLimits."""
    top = _keys(data, "limits", {"schema_version", "robot", "joints", "workspace", "end_effector"})
    if top["schema_version"] != SCHEMA_VERSION:
        raise LimitsError(f"schema_version must be {SCHEMA_VERSION}")
    robot = top["robot"]
    if not isinstance(robot, str) or not robot:
        raise LimitsError("robot: expected a non-empty string")
    joints_table = top["joints"]
    if not isinstance(joints_table, dict) or not joints_table:
        raise LimitsError("joints: at least one joint is required")
    joints: dict[str, JointLimits] = {}
    for name, spec in joints_table.items():
        where = f"joints.{name}"
        spec = _keys(spec, where, {"position", "velocity", "torque"})
        lo, hi = _vec(spec["position"], f"{where}.position", 2)
        if lo >= hi:
            raise LimitsError(f"{where}.position: lower bound must be below upper bound")
        joints[name] = JointLimits(
            position=(lo, hi),
            velocity=_number(spec["velocity"], f"{where}.velocity", positive=True),
            torque=_number(spec["torque"], f"{where}.torque", positive=True),
        )
    ws = _keys(top["workspace"], "workspace", {"min", "max"})
    ws_min = _vec(ws["min"], "workspace.min", 3)
    ws_max = _vec(ws["max"], "workspace.max", 3)
    if any(lo >= hi for lo, hi in zip(ws_min, ws_max, strict=True)):
        raise LimitsError("workspace: each min must be below its max")
    ee = _keys(top["end_effector"], "end_effector", {"max_speed", "max_contact_force"})
    return RobotLimits(
        robot=robot,
        joints=joints,
        workspace_min=ws_min,  # type: ignore[arg-type]
        workspace_max=ws_max,  # type: ignore[arg-type]
        max_ee_speed=_number(ee["max_speed"], "end_effector.max_speed", positive=True),
        max_contact_force=_number(
            ee["max_contact_force"], "end_effector.max_contact_force", positive=True
        ),
    )


def load_limits(path: str | Path) -> RobotLimits:
    """Read and validate a TOML limits file."""
    path = Path(path)
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError as exc:
        raise LimitsError(f"limits file not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise LimitsError(f"{path}: invalid TOML: {exc}") from exc
    return parse_limits(data)
