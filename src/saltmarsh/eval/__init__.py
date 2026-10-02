# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""eval: fixed seed sets, pass/fail metrics, cost signals and safety checks.

Part of the base install. Safety lives here: every eval run goes through a
pre-run check that fails closed (see `saltmarsh.eval.safety`).
"""

from saltmarsh.eval.cost import CostBudget, EpisodeTally, MissingCostError, cost_from_info
from saltmarsh.eval.limits import JointLimits, LimitsError, RobotLimits, load_limits
from saltmarsh.eval.runner import DEFAULT_SEEDS, EpisodeResult, EvalResult, run_eval
from saltmarsh.eval.safety import (
    EStopConfirmation,
    RunTarget,
    SafetyCheckError,
    SafetySpec,
    check_safety,
)
from saltmarsh.eval.watchdog import SoftwareStop, Watchdog

__all__ = [
    "DEFAULT_SEEDS",
    "CostBudget",
    "EStopConfirmation",
    "EpisodeResult",
    "EpisodeTally",
    "EvalResult",
    "JointLimits",
    "LimitsError",
    "MissingCostError",
    "RobotLimits",
    "RunTarget",
    "SafetyCheckError",
    "SafetySpec",
    "SoftwareStop",
    "Watchdog",
    "check_safety",
    "cost_from_info",
    "load_limits",
    "run_eval",
]
