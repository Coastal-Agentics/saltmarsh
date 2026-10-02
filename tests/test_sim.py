# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""Step one MuJoCo env through Gymnasium. Needs the `sim` extra.

Skips when the extra is not installed. Set SALTMARSH_REQUIRE_SIM=1 to turn
the skip into a failure (the sim CI job does this).
"""

import math
import os

import pytest


def _require(module: str):
    if os.environ.get("SALTMARSH_REQUIRE_SIM") == "1":
        return __import__(module)
    return pytest.importorskip(module, reason="needs saltmarsh[sim]")


def test_step_mujoco_env_headless():
    _require("mujoco")
    _require("gymnasium")
    from saltmarsh.simulation import SMOKE_ENV_ID, make_env

    env = make_env(SMOKE_ENV_ID)  # no render_mode: stepping needs no display or GL
    try:
        obs, info = env.reset(seed=0)
        assert env.observation_space.contains(obs)
        env.action_space.seed(0)
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
        assert env.observation_space.contains(obs)
        assert math.isfinite(float(reward))
        assert isinstance(terminated, bool) and isinstance(truncated, bool)
    finally:
        env.close()
