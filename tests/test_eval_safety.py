# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from saltmarsh.eval import (
    EpisodeTally,
    EStopConfirmation,
    RunTarget,
    SafetyCheckError,
    SafetySpec,
    check_safety,
    load_limits,
    run_eval,
)

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "limits" / "example-arm.toml"
CONFIRMED = EStopConfirmation(operator="operator on duty", within_reach=True, tested=True)


def test_sim_runs_pass():
    check_safety(SafetySpec(target=RunTarget.SIM))


def test_hardware_with_confirmed_estop_and_limits_passes():
    check_safety(
        SafetySpec(target=RunTarget.HARDWARE, limits=load_limits(EXAMPLE), estop=CONFIRMED)
    )


@pytest.mark.parametrize(
    "estop",
    [
        None,
        EStopConfirmation(operator="", within_reach=True, tested=True),
        EStopConfirmation(operator="op", within_reach=False, tested=True),
        EStopConfirmation(operator="op", within_reach=True, tested=False),
        EStopConfirmation(operator="op", within_reach=1, tested=1),  # must be exactly True
    ],
)
def test_hardware_without_confirmed_estop_is_refused(estop):
    spec = SafetySpec(target=RunTarget.HARDWARE, limits=load_limits(EXAMPLE), estop=estop)
    with pytest.raises(SafetyCheckError, match="hardware run refused"):
        check_safety(spec)


def test_hardware_without_limits_is_refused():
    with pytest.raises(SafetyCheckError, match="limits"):
        check_safety(SafetySpec(target=RunTarget.HARDWARE, estop=CONFIRMED))


@pytest.mark.parametrize("spec", [None, {}, "sim", SafetySpec(target="sim")])
def test_missing_or_malformed_spec_is_refused(spec):
    with pytest.raises(SafetyCheckError):
        check_safety(spec)


def _boom():
    raise RuntimeError("sensor offline")


@pytest.mark.parametrize("monitor", [lambda: False, lambda: None, lambda: 1, _boom])
def test_monitors_fail_closed(monitor):
    with pytest.raises(SafetyCheckError):
        check_safety(SafetySpec(target=RunTarget.SIM, monitors={"m": monitor}))


def _episode(seed):
    tally = EpisodeTally()
    tally.add(1.0, {"cost": 0.0 if seed % 2 == 0 else 1.0})
    return True, tally


def test_run_eval_scores_cost_alongside_success():
    result = run_eval(_episode, safety=SafetySpec(target=RunTarget.SIM), seeds=range(4))
    assert (result.passed, result.total) == (2, 4)


def test_run_eval_runs_nothing_when_the_check_fails():
    calls = []

    def episode(seed):
        calls.append(seed)
        return _episode(seed)

    with pytest.raises(SafetyCheckError):
        run_eval(episode, safety=SafetySpec(target=RunTarget.HARDWARE))
    with pytest.raises(SafetyCheckError):
        run_eval(episode, safety=None)  # type: ignore[arg-type]
    assert calls == []
