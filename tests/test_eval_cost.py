# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
import math

import pytest

from saltmarsh.eval import CostBudget, EpisodeTally, MissingCostError, cost_from_info


def test_cost_is_read_and_tallied():
    tally = EpisodeTally()
    tally.add(1.0, {"cost": 0.0})
    tally.add(2.0, {"cost": 0.5, "cost_by_kind": {"contact": 0.5}})
    assert (tally.total_reward, tally.total_cost, tally.steps) == (3.0, 0.5, 2)
    assert tally.cost_by_kind == {"contact": 0.5}


@pytest.mark.parametrize(
    ("info", "error"),
    [
        ({}, MissingCostError),
        ({"cost": None}, TypeError),
        ({"cost": True}, TypeError),
        ({"cost": -1.0}, ValueError),
        ({"cost": math.nan}, ValueError),
        ({"cost": math.inf}, ValueError),
    ],
)
def test_bad_or_missing_cost_fails_closed(info, error):
    with pytest.raises(error):
        cost_from_info(info)


def test_budget():
    tally = EpisodeTally()
    tally.add(10.0, {"cost": 1.0})
    assert not CostBudget().passes(tally)  # default budget is zero cost
    assert CostBudget(max_total_cost=1.0).passes(tally)
    with pytest.raises(ValueError):
        CostBudget(max_total_cost=-1)
