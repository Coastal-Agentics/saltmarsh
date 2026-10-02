# ADR-001: Packaging, parts and v0.1 scope

- **Status:** Accepted
- **Date:** 2026-10-02

## Context

Saltmarsh needs a structure and a packaging model before any real code lands. The architecture is described in [ARCHITECTURE.md](../../ARCHITECTURE.md). This record fixes the decisions behind it.

## Decisions

1. **One distribution, seven parts.** A single Python distribution, `saltmarsh`, is built from this monorepo. Its parts are `data`, `perception`, `movement`, `behavior`, `simulation`, `gaming` and `eval`.

2. **Base install and extras.** `pip install saltmarsh` provides `data` and `eval` only, with no third-party dependencies. The extras are `[sim]`, `[behavior]`, `[perception]`, `[movement]`, `[ros]`, `[gaming]` and `[all]`.

3. **Safety lives in eval and is enforced.** Every eval run goes through a pre-run check (`saltmarsh.eval.safety.check_safety`) that fails closed and cannot be skipped. Sim runs pass. Hardware runs are refused unless a named operator confirms a tested physical e-stop within reach and a validated per-robot limits file is loaded. Also in eval:
   - cost signals reported alongside reward, where a missing cost is an error;
   - a strict limits-file loader;
   - a runtime watchdog with a latched software stop.

4. **Exact pins for pre-1.0 upstreams.** Both pins were checked on PyPI on 2026-10-02:
   - **LeRobot `0.6.1`.** This is the latest release (2026-08-03). It requires Python >= 3.12 and constrains `torch>=2.7,<2.12`, so PyTorch resolves to 2.11.0, not the newest 2.14.1.
   - **Rerun `rerun-sdk==0.33.1`.** This is the newest Rerun inside LeRobot 0.6.1's declared range: its `viz` extra requires `rerun-sdk>=0.24,<0.34`. Rerun 0.38.1 is the latest release and also resolves next to LeRobot, because LeRobot's base install does not depend on Rerun. However, it falls outside the range LeRobot tests its own Rerun tooling against, and it would conflict with anyone who also installs `lerobot[viz]`. We will move to a newer Rerun when LeRobot widens that range.
   - `pip install ".[all]"` was resolved on Python 3.12 and 3.13 and installed on 3.12. Other dependencies use compatible ranges rather than exact pins.

5. **Python.** `requires-python = ">=3.12"`, because LeRobot 0.6.1 requires 3.12. CI tests 3.12 and 3.13.

6. **PyTorch only for v0.1.** JAX (MJX, MuJoCo Playground) is out of scope for v0.1.

7. **ROS 2 is optional.** `rclpy` is not on PyPI; it comes from a ROS 2 installation. The `[ros]` extra therefore lists no dependencies. It marks the bridge as supported. `saltmarsh.movement.ros` checks for `rclpy` at runtime and explains the setup when it is missing. No fake or third-party repackaged `rclpy` is depended on.

8. **The tank engine stays in Rust.** The engine stays a crate in starscream-agentics/arena. It will ship as a separate `saltmarsh-arena` wheel built with PyO3 and maturin, and `[gaming]` will then depend on it. Until that wheel is published, no extra names it, so `pip install ".[all]"` keeps working. `gaming` is a stub with a clear error for the arena env. `gaming` uses py_trees for behavior trees, pinned to `py_trees==2.6.0` (BSD-3-Clause, pure Python, the latest release).

9. **behavior builds on MuJoCo-native motion imitation.** Policies are trained to follow reference motion under MuJoCo physics. Because of decision 6, MJX-based training waits until JAX is in scope.

10. **Licensing.**
    - **Code:** Apache-2.0.
    - **Models we train and publish:** Apache-2.0.
    - **Datasets we record and publish:** CC BY 4.0 (`CC-BY-4.0`).
    - **Per-file licensing:** every file carries SPDX information, and the repository is REUSE-compliant: Python and TOML files carry headers, and other files are covered by `REUSE.toml`.
    - **Contributions:** made under the Developer Certificate of Origin, so each commit is signed off. There is no CLA.

11. **License gate in data.** Every asset on a provenance card records an SPDX license expression. The gate refuses non-commercial (NC) and no-derivatives (ND) licenses. It also refuses anything not on its allowlist, including copyleft data licenses such as CC-BY-SA, unknown ids, `NOASSERTION` and `LicenseRef-*`. There is no opt-in override in v0.1.

12. **No publishing yet.** Nothing is uploaded to PyPI, and no release or tag is created as part of this work.

## Consequences

- The base install is small and fast to test. Heavy stacks are tested in their own CI jobs.
- LeRobotDataset I/O needs `[behavior]`, because LeRobot depends on PyTorch. The base `data` part covers provenance and licensing without it.
- Moving LeRobot or Rerun is a deliberate change to `pyproject.toml` and this record.
