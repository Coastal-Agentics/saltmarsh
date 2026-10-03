# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""A minimal eval runner. The safety check runs first; nothing runs if it fails."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from saltmarsh.eval.cost import CostBudget, EpisodeTally
from saltmarsh.eval.safety import SafetySpec, check_safety

#: A fixed default seed set, so results are comparable between runs.
DEFAULT_SEEDS: tuple[int, ...] = tuple(range(10))


@dataclass(frozen=True)
class EpisodeResult:
    seed: int
    task_success: bool
    tally: EpisodeTally
    within_budget: bool

    @property
    def passed(self) -> bool:
        return self.task_success and self.within_budget


@dataclass(frozen=True)
class EvalResult:
    episodes: tuple[EpisodeResult, ...]

    @property
    def passed(self) -> int:
        return sum(e.passed for e in self.episodes)

    @property
    def total(self) -> int:
        return len(self.episodes)


def run_eval(
    episode: Callable[[int], tuple[bool, EpisodeTally]],
    *,
    safety: SafetySpec,
    seeds: Iterable[int] = DEFAULT_SEEDS,
    budget: CostBudget | None = None,
) -> EvalResult:
    """Run `episode(seed)` for each seed after the pre-run safety check passes.

    `episode` returns (task_success, tally). An episode passes only if the
    task succeeded and its cost stayed within `budget` (default: zero cost).
    """
    check_safety(safety)
    budget = budget or CostBudget()
    results = []
    for seed in seeds:
        success, tally = episode(seed)
        results.append(
            EpisodeResult(
                seed=seed,
                task_success=bool(success),
                tally=tally,
                within_budget=budget.passes(tally),
            )
        )
    return EvalResult(episodes=tuple(results))
