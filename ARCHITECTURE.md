# Architecture

Saltmarsh has seven parts. Five follow how the robotics work divides: perception, movement, behavior, simulation and gaming. Two cut across all of them: **data**, which every part reads and writes, and **eval**, which decides whether anything worked and enforces safety.

Hardware and sim-to-real are not separate parts. LeRobot already puts real and simulated robots behind one `Robot` interface, which belongs in movement. Sim-to-real is a simulation technique that eval measures.

## Parts

| Part | Holds | Builds on | Install |
|---|---|---|---|
| `data` | LeRobotDataset v3 I/O, provenance cards, project spec, license gate | LeRobot datasets | base (LeRobot I/O: `[behavior]`) |
| `perception` | cameras, depth, point clouds, top-down maps | Open3D, Rerun | `[perception]` |
| `movement` | kinematics, IK, controllers, robot interfaces (real and sim), optional ROS 2 bridge | LeRobot `Robot`, mink, Pinocchio, rclpy (optional) | `[movement]`, `[ros]` |
| `behavior` | policies, imitation and RL training, reward functions | MuJoCo-native motion imitation, LeRobot policies, Stable-Baselines3, PyTorch | `[behavior]` |
| `simulation` | worlds, physics, robot models, sim-to-real (randomization, calibration) | MuJoCo, Gymnasium, MuJoCo Menagerie models | `[sim]` |
| `gaming` | arenas, multi-agent self-play, browser demos | PettingZoo, py_trees, the arena engine (via `saltmarsh-arena`, planned) | `[gaming]` |
| `eval` | fixed seed sets, pass/fail metrics, cost signals, limits, watchdog, pre-run safety check | Gymnasium/PettingZoo seeding; Safety-Gymnasium as a reference only | base |

## Dependency rules

- `data` and `eval` import only the Python standard library. `import saltmarsh` and importing any part never imports a heavy dependency. A test checks this (`tests/test_smoke.py`).
- Each optional part imports its dependencies inside the functions that use them. When the extra is missing, it raises `MissingExtraError`, which names the extra to install.
- Other parts may depend on `data` and `eval`. `data` and `eval` do not depend on the other parts.
- CleanRL publishes no recent releases, so any of its single-file implementations that Saltmarsh uses will be copied in with attribution rather than added as a dependency.

## Upstream projects

All of them use permissive licenses (MIT, Apache-2.0 or BSD).

| Project | License | Used by |
|---|---|---|
| [LeRobot](https://github.com/huggingface/lerobot) | Apache-2.0 | data, movement, behavior, eval |
| [Rerun](https://github.com/rerun-io/rerun) | MIT OR Apache-2.0 | perception (viewing) |
| [Open3D](https://github.com/isl-org/Open3D) | MIT | perception |
| [mink](https://github.com/kevinzakka/mink) | Apache-2.0 | movement |
| [Pinocchio](https://github.com/stack-of-tasks/pinocchio) | BSD-2-Clause | movement |
| [rclpy](https://github.com/ros2/rclpy) | Apache-2.0 | movement (optional, not on PyPI) |
| [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) | MIT | behavior |
| [MuJoCo](https://github.com/google-deepmind/mujoco) | Apache-2.0 | simulation, behavior |
| [Gymnasium](https://github.com/Farama-Foundation/Gymnasium) | MIT | simulation, eval |
| [PettingZoo](https://github.com/Farama-Foundation/PettingZoo) | MIT | gaming, eval |
| [py_trees](https://github.com/splintered-reality/py_trees) | BSD-3-Clause | gaming |
| [PyO3](https://github.com/PyO3/pyo3), [maturin](https://github.com/PyO3/maturin) | MIT OR Apache-2.0 | `saltmarsh-arena` build (planned) |

LeRobot and Rerun are pre-1.0 and change quickly, so they are pinned to exact versions. See [ADR-001](docs/adr/ADR-001-packaging-and-scope.md).

## Packaging

One distribution, `saltmarsh`, is built from this monorepo with optional extras. This follows LeRobot's own extras pattern and avoids version skew between many small packages. A part should be split into its own package only if outside users want it without the rest.

## Safety contract (eval)

Safety is enforced in `eval`, not left to convention:

1. **Cost alongside reward.** Every env step reports a non-negative `cost` in its `info` dict. A missing cost is an error, never zero. An episode passes only if the task succeeds and total cost stays within the budget, which defaults to zero.
2. **Per-robot limits file.** This is a TOML file with joint position, velocity and torque limits, a workspace box, an end-effector speed cap and a contact force cap. The loader rejects missing, unknown, non-numeric, non-finite or inconsistent values. See `examples/limits/example-arm.toml`; its numbers are placeholders.
3. **Runtime watchdog.** Every command goes through `Watchdog.guard`. A stale command stream, a software stop or a limit violation latches a stop that only an explicit `reset` clears.
4. **Pre-run check.** `run_eval` calls `check_safety` before the first episode, and there is no way to skip it. Sim runs pass. Hardware runs need an `EStopConfirmation` from a named operator stating that a physical e-stop is within reach and has been tested, plus a validated limits file. Any extra monitor must return exactly `True`.

Planned for later releases: rollout logs (seed, policy hash, limits file, cost totals, violations, stops), a safety section on provenance cards, specification-gaming checks, a sim-to-sim gate before hardware, and a hardware gate.

## Rust: the tank arena

- The tank engine stays a Rust crate in [starscream-agentics/arena](https://github.com/starscream-agentics/arena).
- It will be wrapped with PyO3 and built with maturin as a separate compiled wheel, `saltmarsh-arena`. It will be exposed as a Gymnasium env (one agent) and a PettingZoo parallel env (several agents).
- Once that wheel is published, `[gaming]` will depend on it. Until then, `saltmarsh.gaming.make_arena_env` raises a clear error, and no extra refers to the unpublished package, so `pip install ".[all]"` keeps working.
- A separate wheel keeps the pure-Python core simple to build and release.
- `mujoco-rs` stays out of the core. It may be used for Rust-side replay tools only.
