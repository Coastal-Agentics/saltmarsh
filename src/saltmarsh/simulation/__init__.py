# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""simulation: worlds, physics, robot models and sim-to-real tools (stub).

MuJoCo environments through Gymnasium. Needs the `sim` extra.
"""

from typing import Any

from saltmarsh._extras import require

#: The env used by the smoke test: a small MuJoCo model that needs no rendering.
SMOKE_ENV_ID = "InvertedPendulum-v5"


def make_env(env_id: str = SMOKE_ENV_ID, **kwargs: Any) -> Any:
    """Create a Gymnasium env. MuJoCo envs need the `sim` extra."""
    require("mujoco", "sim")
    gymnasium = require("gymnasium", "sim")
    return gymnasium.make(env_id, **kwargs)


__all__ = ["SMOKE_ENV_ID", "make_env"]
