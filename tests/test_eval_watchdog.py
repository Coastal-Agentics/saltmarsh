# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

import pytest

from saltmarsh.eval import SoftwareStop, Watchdog, load_limits

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "limits" / "example-arm.toml"


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_fresh_commands_pass():
    clock = FakeClock()
    dog = Watchdog(0.1, clock=clock)
    for _ in range(5):
        clock.now += 0.05
        assert dog.guard("cmd") == "cmd"
    assert not dog.stopped


def test_timeout_stops_and_latches():
    clock = FakeClock()
    dog = Watchdog(0.1, clock=clock)
    clock.now = 0.2
    assert dog.stopped
    assert "timeout" in dog.stop_reason
    with pytest.raises(SoftwareStop, match="timeout"):
        dog.guard("cmd")
    with pytest.raises(SoftwareStop):  # still stopped: the stop latches
        dog.guard("cmd")
    dog.reset()
    assert dog.guard("cmd") == "cmd"


def test_software_stop():
    dog = Watchdog(1.0, clock=FakeClock())
    dog.stop("operator pressed stop")
    with pytest.raises(SoftwareStop, match="operator pressed stop"):
        dog.guard("cmd")


def test_limit_violation_stops():
    dog = Watchdog(1.0, limits=load_limits(EXAMPLE), clock=FakeClock())
    assert dog.guard("ok", joint_position={"elbow": 0.0}) == "ok"
    with pytest.raises(SoftwareStop, match="limit violation"):
        dog.guard("too far", joint_position={"elbow": 3.0})
    with pytest.raises(SoftwareStop):
        dog.guard("ok", joint_position={"elbow": 0.0})


def test_timeout_must_be_positive():
    with pytest.raises(ValueError):
        Watchdog(0)
