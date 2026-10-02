# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""Cost signals reported alongside reward.

Every env step reports a non-negative cost next to its reward (contacts,
joint-limit hits, excess speed or force, falls), as in Safety-Gymnasium. An
episode that wins on reward but goes over its cost budget fails.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


class MissingCostError(KeyError):
    """Raised when a step does not report a cost. Missing cost is never treated as zero."""


def cost_from_info(info: Mapping[str, Any]) -> float:
    """Read the step cost from a Gymnasium `info` dict (key `"cost"`).

    Fails closed: a missing, non-numeric, negative or non-finite cost raises.
    """
    if "cost" not in info:
        raise MissingCostError("step info has no 'cost'; every env must report one")
    cost = info["cost"]
    if isinstance(cost, bool) or not isinstance(cost, int | float):
        raise TypeError(f"cost must be a number, got {type(cost).__name__}")
    cost = float(cost)
    if not math.isfinite(cost) or cost < 0:
        raise ValueError(f"cost must be finite and >= 0, got {cost}")
    return cost


@dataclass
class EpisodeTally:
    """Running totals of reward and cost for one episode."""

    total_reward: float = 0.0
    total_cost: float = 0.0
    steps: int = 0
    cost_by_kind: dict[str, float] = field(default_factory=dict)

    def add(self, reward: float, info: Mapping[str, Any]) -> None:
        cost = cost_from_info(info)
        self.total_reward += float(reward)
        self.total_cost += cost
        self.steps += 1
        for kind, value in (info.get("cost_by_kind") or {}).items():
            self.cost_by_kind[kind] = self.cost_by_kind.get(kind, 0.0) + float(value)


@dataclass(frozen=True)
class CostBudget:
    """The most cost an episode may accumulate and still pass."""

    max_total_cost: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.max_total_cost) or self.max_total_cost < 0:
            raise ValueError("max_total_cost must be finite and >= 0")

    def passes(self, tally: EpisodeTally) -> bool:
        return tally.total_cost <= self.max_total_cost
