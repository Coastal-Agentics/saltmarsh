# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""gaming: arenas, multi-agent self-play and browser demos (stub).

Agent logic in arenas uses behavior trees through py_trees. Multi-agent envs
follow PettingZoo's parallel API. Needs the `gaming` extra.

The tank engine stays a Rust crate in starscream-agentics/arena. It will ship
as a separate compiled wheel, `saltmarsh-arena` (PyO3 + maturin), exposed as a
Gymnasium env and a PettingZoo parallel env, and the `gaming` extra will then
depend on it. That wheel is not published yet, so nothing here depends on it.
"""

import importlib.util
from typing import Any

from saltmarsh._extras import MissingExtraError, require

ARENA_MODULE = "saltmarsh_arena"


def arena_available() -> bool:
    """True if the `saltmarsh-arena` wheel is installed."""
    return importlib.util.find_spec(ARENA_MODULE) is not None


def make_arena_env(**kwargs: Any) -> Any:
    """Create a tank arena env. Raises until `saltmarsh-arena` is published."""
    if not arena_available():
        raise MissingExtraError(
            "saltmarsh-arena is not published yet. The tank engine lives in "
            "starscream-agentics/arena and will ship as a separate wheel."
        )
    raise NotImplementedError("arena bindings are planned; see ARCHITECTURE.md")


def py_trees() -> Any:
    """Return the `py_trees` module, installed by the `gaming` extra."""
    return require("py_trees", "gaming")


__all__ = ["ARENA_MODULE", "arena_available", "make_arena_env", "py_trees"]
