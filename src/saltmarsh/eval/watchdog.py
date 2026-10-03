# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""Runtime watchdog and software stop.

The watchdog sits between policy and robot. Every command must pass through
`Watchdog.guard`. If no fresh command arrives within the timeout, or a
software stop has been issued, or the command breaks the robot's limits, the
watchdog latches into the stopped state and refuses all further commands until
an operator calls `reset`.
"""

import time
from collections.abc import Callable, Mapping
from typing import Any

from saltmarsh.eval.limits import RobotLimits


class SoftwareStop(RuntimeError):
    """Raised when a command is refused because the watchdog is stopped."""


class Watchdog:
    def __init__(
        self,
        timeout_s: float,
        *,
        limits: RobotLimits | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not timeout_s > 0:
            raise ValueError("timeout_s must be > 0")
        self.timeout_s = float(timeout_s)
        self.limits = limits
        self._clock = clock
        self._last_feed = clock()
        self._stop_reason: str | None = None

    @property
    def stopped(self) -> bool:
        self._check_timeout()
        return self._stop_reason is not None

    @property
    def stop_reason(self) -> str | None:
        self._check_timeout()
        return self._stop_reason

    def stop(self, reason: str = "software stop") -> None:
        """Issue a software stop. Latches until `reset`."""
        if self._stop_reason is None:
            self._stop_reason = reason

    def reset(self) -> None:
        """Clear a stop. Meant for an operator, after the cause is understood."""
        self._stop_reason = None
        self._last_feed = self._clock()

    def _check_timeout(self) -> None:
        if self._stop_reason is None and self._clock() - self._last_feed > self.timeout_s:
            self._stop_reason = f"watchdog timeout: no command for over {self.timeout_s}s"

    def guard(self, command: Any, **state: Mapping[str, float] | float | None) -> Any:
        """Pass `command` through if it is safe to send; otherwise stop and raise.

        `state` is forwarded to `RobotLimits.violations` (for example
        `joint_position={...}`) when limits are set.
        """
        self._check_timeout()
        if self._stop_reason is not None:
            raise SoftwareStop(self._stop_reason)
        if self.limits is not None:
            problems = self.limits.violations(**state)  # type: ignore[arg-type]
            if problems:
                self.stop("limit violation: " + "; ".join(problems))
                raise SoftwareStop(self._stop_reason)
        self._last_feed = self._clock()
        return command
