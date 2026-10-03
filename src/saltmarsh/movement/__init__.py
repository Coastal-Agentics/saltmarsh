# SPDX-FileCopyrightText: 2026 Nye Warburton
# SPDX-License-Identifier: Apache-2.0
"""movement: kinematics, IK, controllers and robot interfaces (stub).

Real and simulated robots sit behind LeRobot's `Robot` interface. Needs the
`movement` extra (LeRobot, mink for MuJoCo IK, Pinocchio). The optional ROS 2
bridge is in `saltmarsh.movement.ros`.
"""

from typing import Any

from saltmarsh._extras import require


def robot_interface() -> Any:
    """Return LeRobot's `Robot` base class, installed by the `movement` extra."""
    return require("lerobot.robots", "movement").Robot


__all__ = ["robot_interface"]
