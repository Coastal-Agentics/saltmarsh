# Saltmarsh

Saltmarsh is a Python library for physical AI: robot simulation, datasets, learned behavior and evaluation, built on [MuJoCo](https://github.com/google-deepmind/mujoco), [Gymnasium](https://github.com/Farama-Foundation/Gymnasium) and [LeRobot](https://github.com/huggingface/lerobot).

**Status: v0.1 scaffold.** The package layout, extras and safety checks are in place. Most parts are stubs. Nothing is published to PyPI yet, so install from a clone.

## Install

Requires Python 3.12 or newer (LeRobot 0.6 needs 3.12). Linux is the tested platform.

```bash
git clone https://github.com/Coastal-Agentics/saltmarsh
cd saltmarsh
pip install .            # data + eval only, no third-party dependencies
pip install ".[sim]"     # add MuJoCo + Gymnasium
pip install ".[all]"     # everything that is on PyPI
```

| Extra | Adds | Main dependencies |
|---|---|---|
| *(base)* | `data`, `eval` | none |
| `[sim]` | `simulation` | `gymnasium[mujoco]`, `mujoco` |
| `[behavior]` | `behavior`, LeRobotDataset I/O in `data` | `lerobot[dataset]==0.6.1`, `torch`, `stable-baselines3` |
| `[perception]` | `perception` | `rerun-sdk==0.33.1`, `open3d` |
| `[movement]` | `movement` | `lerobot==0.6.1`, `mink`, `pin` (Pinocchio) |
| `[ros]` | ROS 2 bridge in `movement` | none from PyPI (see [ROS 2](#ros-2)) |
| `[gaming]` | `gaming` | `pettingzoo`, `py_trees==2.6.0` |
| `[all]` | all of the above | |

Open3D (in `[perception]`) loads the system EGL library, so on a minimal Linux install add it first (Debian/Ubuntu: `sudo apt install libegl1`).

LeRobot and Rerun are pre-1.0 and change quickly, so they are pinned to exact versions. Why these versions is recorded in [ADR-001](docs/adr/ADR-001-packaging-and-scope.md). PyTorch is the only deep-learning framework in v0.1.

## Parts

**data.** Reads and writes the data every other part uses. It holds LeRobotDataset v3 I/O, provenance cards and the project spec. Every asset on a provenance card records an SPDX license. A license gate refuses non-commercial (NC) and no-derivatives (ND) licenses, and anything it does not recognize, before data is loaded. It is part of the base install. LeRobotDataset I/O needs `[behavior]`, because LeRobot depends on PyTorch.

**perception.** Cameras, depth, point clouds and top-down maps. It uses Rerun for viewing and Open3D for point clouds. Needs `[perception]`.

**movement.** Kinematics, inverse kinematics, controllers and robot interfaces. Real and simulated robots sit behind LeRobot's `Robot` interface. IK uses mink (MuJoCo) and Pinocchio. An optional ROS 2 bridge lives in `saltmarsh.movement.ros`. Needs `[movement]`.

**behavior.** Policies, imitation and reinforcement learning, and reward functions. It builds on MuJoCo-native motion imitation: a policy controls a simulated body under MuJoCo physics so that it follows reference motion. It also uses LeRobot policies and Stable-Baselines3. PyTorch only. Needs `[behavior]`.

**simulation.** Worlds, physics, robot models and sim-to-real tools such as domain randomization and calibration. MuJoCo environments are exposed through Gymnasium. Needs `[sim]`.

**gaming.** Arenas, multi-agent self-play and browser demos. Agent logic uses behavior trees through py_trees, and multi-agent envs follow PettingZoo's parallel API. The tank engine is a Rust crate in [starscream-agentics/arena](https://github.com/starscream-agentics/arena). It will ship as a separate `saltmarsh-arena` wheel that `[gaming]` will depend on. That wheel is not published yet, so for now gaming is a stub. Needs `[gaming]`.

**eval.** Fixed seed sets, pass/fail metrics, cost signals and safety checks. Every env step reports a cost alongside its reward, and an episode that goes over its cost budget fails. Each robot has a limits file, which a strict loader validates. A runtime watchdog sits between policy and robot. It stops when commands go stale or break the limits, and it offers a software stop. Every eval run first passes a pre-run check that fails closed. Sim runs pass. Hardware runs are refused unless a named operator has confirmed a tested physical e-stop within reach and a limits file is loaded. It is part of the base install.

See [ARCHITECTURE.md](ARCHITECTURE.md) for how the parts depend on each other.

## ROS 2

`rclpy` is not distributed on PyPI, so `pip install "saltmarsh[ros]"` installs nothing extra. The extra marks the bridge as a supported option. To use the bridge:

1. Install ROS 2 from its official packages. For example, ROS 2 Jazzy on Ubuntu 24.04 uses the system Python 3.12.
2. Run `source /opt/ros/jazzy/setup.bash`.
3. Install Saltmarsh into an environment that can see ROS 2's Python packages, e.g. `python3 -m venv --system-site-packages .venv`.

`saltmarsh.movement.ros.rclpy()` raises an error that explains these steps when `rclpy` is not importable. ROS 2 is optional and is not a focus for v0.1.

## Development

```bash
pip install -e . --group dev      # pytest and ruff (needs pip >= 25.1)
pytest                            # the MuJoCo test skips without [sim]
ruff check . && ruff format --check .
pip install --group reuse && reuse lint
```

The CI jobs are specified in [docs/ci-spec.md](docs/ci-spec.md).

## Licensing

- **Code** is Apache-2.0 (see [LICENSE](LICENSE) and [NOTICE](NOTICE)).
- **Models** that Saltmarsh trains and publishes are Apache-2.0.
- **Datasets** that Saltmarsh records and publishes are CC BY 4.0 (SPDX `CC-BY-4.0`).

Every file carries SPDX license information, and the repository follows the [REUSE](https://reuse.software/) specification (`reuse lint`). Contributions are accepted under the Developer Certificate of Origin: sign off each commit with `git commit -s`. See [GOVERNANCE.md](GOVERNANCE.md).
