# Third-party notices

Saltmarsh's base install has **no third-party dependencies**. The optional extras (`sim`, `behavior`, `perception`, `movement`, `gaming`) install packages from PyPI that keep their own licenses. Saltmarsh does not bundle or redistribute them.

| Extra | Packages | License (PyPI metadata, 2026-10-03) |
|---|---|---|
| sim | gymnasium, mujoco | MIT; Apache-2.0 |
| behavior | lerobot 0.6.1, torch, stable-baselines3, gymnasium | Apache-2.0; BSD-style/Apache-2.0; MIT; MIT |
| perception | rerun-sdk 0.33.1, open3d, numpy | MIT OR Apache-2.0; MIT; BSD-3-Clause |
| movement | lerobot 0.6.1, mink, pin (Pinocchio) | Apache-2.0; Apache-2.0; BSD-3-Clause |
| gaming | pettingzoo, gymnasium, py_trees 2.6.0 | MIT; MIT; BSD-3-Clause |
| dev tools (not installed with the package) | pytest, ruff, reuse 6.2.0, hatchling | MIT; MIT; GPL-3.0-or-later (CLI only); MIT |

Some of these wheels include native libraries under their own terms. For example, video decoding stacks pulled in by LeRobot can include FFmpeg under the LGPL. **Anyone who builds a bundle or container image that includes them must follow those terms.**
