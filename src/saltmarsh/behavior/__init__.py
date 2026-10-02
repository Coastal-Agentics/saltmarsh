# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""behavior: policies, imitation and RL training, reward functions (stub).

Builds on MuJoCo-native motion imitation (a policy controls a simulated body
under MuJoCo physics so that it follows reference motion), plus LeRobot
policies and Stable-Baselines3. PyTorch only for v0.1. Needs the `behavior`
extra.
"""

from typing import Any

from saltmarsh._extras import require


def torch() -> Any:
    """Return the `torch` module, installed by the `behavior` extra."""
    return require("torch", "behavior")


def stable_baselines3() -> Any:
    """Return the `stable_baselines3` module, installed by the `behavior` extra."""
    return require("stable_baselines3", "behavior")


__all__ = ["stable_baselines3", "torch"]
