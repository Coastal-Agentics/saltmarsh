# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""The pre-run safety check. It runs before every eval run and fails closed.

- Sim runs pass once the spec itself is valid.
- Hardware runs are refused unless a physical e-stop within reach has been
  confirmed (and tested) by a named operator, and a validated limits file is
  loaded.
- Any extra monitor callables must each return exactly `True`; a monitor that
  returns anything else, or raises, fails the check.

There is no flag to skip the check.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

from saltmarsh.eval.limits import RobotLimits


class SafetyCheckError(RuntimeError):
    """Raised when the pre-run check refuses a run."""


class RunTarget(Enum):
    SIM = "sim"
    HARDWARE = "hardware"


@dataclass(frozen=True)
class EStopConfirmation:
    """An operator's statement that a physical e-stop is within reach and was tested."""

    operator: str
    within_reach: bool
    tested: bool


@dataclass(frozen=True)
class SafetySpec:
    target: RunTarget
    limits: RobotLimits | None = None
    estop: EStopConfirmation | None = None
    monitors: Mapping[str, Callable[[], bool]] = field(default_factory=dict)


def check_safety(spec: object) -> None:
    """Raise SafetyCheckError unless `spec` allows the run to start."""
    if not isinstance(spec, SafetySpec):
        raise SafetyCheckError("a SafetySpec is required before any eval run")
    if not isinstance(spec.target, RunTarget):
        raise SafetyCheckError(f"unknown run target: {spec.target!r}")
    if spec.target is RunTarget.HARDWARE:
        estop = spec.estop
        if not isinstance(estop, EStopConfirmation):
            raise SafetyCheckError("hardware run refused: no physical e-stop confirmation")
        if not (isinstance(estop.operator, str) and estop.operator.strip()):
            raise SafetyCheckError("hardware run refused: e-stop confirmation names no operator")
        if estop.within_reach is not True or estop.tested is not True:
            raise SafetyCheckError(
                "hardware run refused: the physical e-stop must be within reach and tested"
            )
        if not isinstance(spec.limits, RobotLimits):
            raise SafetyCheckError("hardware run refused: no validated limits file loaded")
    for name, monitor in spec.monitors.items():
        try:
            ok = monitor()
        except Exception as exc:  # fail closed on any monitor error
            raise SafetyCheckError(f"monitor {name!r} raised: {exc!r}") from exc
        if ok is not True:
            raise SafetyCheckError(f"monitor {name!r} did not report ready")
