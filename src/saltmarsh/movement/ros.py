# SPDX-FileCopyrightText: 2026 Coastal Agentics
# SPDX-License-Identifier: Apache-2.0
"""Optional ROS 2 bridge (stub).

rclpy is not on PyPI. It comes from a ROS 2 installation (for example ROS 2
Jazzy on Ubuntu 24.04, which uses the system Python 3.12). The `ros` extra
therefore installs nothing; it marks the bridge as a supported option. To use
it, source your ROS 2 setup script and install saltmarsh into an environment
that can see that Python's packages, e.g. a venv made with
`--system-site-packages`.
"""

import importlib.util
from typing import Any

from saltmarsh._extras import MissingExtraError


def rclpy_available() -> bool:
    """True if rclpy can be imported in this environment."""
    return importlib.util.find_spec("rclpy") is not None


def rclpy() -> Any:
    """Return the `rclpy` module, or raise with instructions if ROS 2 is not set up."""
    if not rclpy_available():
        raise MissingExtraError(
            "rclpy is not importable. It is not on PyPI; install ROS 2, source its "
            "setup script, and use a Python environment that can see ROS 2's packages."
        )
    import rclpy as module

    return module
