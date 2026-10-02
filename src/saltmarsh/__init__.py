# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""Saltmarsh: simulation, data, behavior and evaluation tools for physical AI.

Importing this package, or any of its seven parts, never imports a heavy
dependency (PyTorch, MuJoCo, Gymnasium, LeRobot, Rerun and so on). Each part
imports those lazily, inside the functions that need them, and raises a clear
error naming the extra to install when they are missing.
"""

__version__ = "0.1.0.dev0"

#: The seven parts. `data` and `eval` work with the base install; the others
#: need their extra (for example `pip install "saltmarsh[sim]"`).
PARTS = ("data", "perception", "movement", "behavior", "simulation", "gaming", "eval")

__all__ = ["PARTS", "__version__"]
