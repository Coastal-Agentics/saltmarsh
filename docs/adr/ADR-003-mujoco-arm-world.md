# ADR-003: The MuJoCo arm world

- **Status:** Proposed
- **Date:** 2026-10-06

## Context

The first Saltmarsh world is a robot arm proof of concept: the SO-101 arm from [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101) picks a cube and places it on a goal. Physics and behavior run here in Python. The arena web viewer plays the result back in 3D. Arena's `docs/STATE.md` lists "Saltmarsh MuJoCo world" as a gate for Nye, and this record is the proposal for that gate. It adds no code and no dependencies.

The plan comes from Reflector's finding "Robot Arm POC with MuJoCo and Our Engine" (2026-10-06). Facts from it that this record relies on, all measured on the box with MuJoCo 3.15.0:

- **A prototype works.** py_trees 2.6.0, mink 1.3.0 and MuJoCo 3.15.0 picked the cube in the Menagerie SO-101 box scene and released it at (0.225, 0.148) m against a goal of (0.22, 0.15) m, about 5 mm off. That is one seed and one run, not a success rate. The SO-101 has 5 arm joints, so IK trades position against orientation, and grasp targets need tuning.
- **Actions don't replay across builds.** With identical control inputs, native MuJoCo and the official wasm build stopped being bit-identical at **step 41**. The largest difference over 5,000 steps (25 s, up to 17 contacts) was 1.7e-15, and contact-rich grasps can amplify such differences. MuJoCo's own docs promise exact reproducibility only "within a single version, on the same architecture".
- **States do replay.** Replaying a recorded qpos log in wasm (`mj_forward`) gave body poses within **4.4e-16** of native.

So the world records **states, not actions**.

Related records: ADR-001 (packaging, safety, licensing), ADR-002 (the Decider), and arena ADR-017 (Proposed, [Coastal-Agentics/arena](https://github.com/Coastal-Agentics/arena)): one three.js page in the arena viewer for state-log playback, with engine-wasm owning the timeline.

## Decisions

### 1. The stack

- **Robot:** Menagerie `robotstudio_so101` (Apache-2.0): 5 arm joints, a gripper, 6 position actuators, and a wrist camera in the MJCF. The real arm costs about $299.
- **Physics:** MuJoCo 3.x in Python.
- **IK:** mink, a `FrameTask` on the `gripperframe` site plus a `PostureTask`, solved with `daqp`.
- **Behavior:** a py_trees tree of skills (`choose_target → above → descend → close → lift → carry → release → home`). Choosing the target is a decision in ADR-002's sense. The default `py_trees` Decider backend answers it, and the decision log sidecar from ADR-002 records it once `behavior.decider` exists. Until then the tree is called directly.
- **Viewer:** arena's 3D page plays the state log (section 5). MuJoCo is not shipped to the browser.
- **Later, not in this record:** live physics in the browser with `@mujoco/mujoco`, learned policies (LeRobot ACT), a Bevy renderer, and hardware. Each needs its own decision. Hardware also needs its own gate.

### 2. The world gate

The world is accepted when all of these are true:

1. **Pinned versions.** `mujoco==3.15.0`, `mink==1.3.0`, `py_trees==2.6.0`, Python 3.12, and Menagerie commit `f054586a8e90465d49ee5be15335c4a0c7f57caf` (2026-10-05). Every state log records these, plus the resolved versions of `numpy`, `qpsolvers` and `daqp`, because they can change the trajectory.
2. **Deterministic.** The same seed, pins and platform give a byte-identical state log. A test runs one seed twice and compares the `log_hash` values. Identical results across platforms are not promised, which is why logs carry states.
3. **A seeded task and a success metric.**
   - The seed drives a `numpy.random.Generator(PCG64(seed))`. In a fixed order, it draws the cube's start position (x 0.20–0.30 m, y −0.10–0.05 m, at least 0.06 m from the goal) and its yaw (±45°). The goal is fixed at (0.22, 0.15) m. P1 may tune these ranges before the gate run. The gate then fixes them as `world_version` 1.
   - **Success:** at the end of the episode (at most 600 frames, which is 20 s at 30 Hz), the cube's centre is within 0.02 m of the goal in x and y. It must also be resting on the floor (z within 0.005 m of 0.03 m, speed under 0.01 m/s) with the gripper open.
   - **P1 target:** at least 90% success (45 of 50) over seeds 0–49, run through `saltmarsh.eval.run_eval`.
4. **Assets verified.** The Menagerie files come from the pinned commit and match the SHA-256 lock (section 4). A provenance card for the model passes the `data` license gate (Apache-2.0 is on the allowlist).
5. **Safety and the Watchdog still apply in sim.**
   - Every eval goes through `run_eval`, so `check_safety` runs first. A `RunTarget.SIM` spec passes, and there is still no way to skip it.
   - Every control command goes through `Watchdog.guard` with an SO-101 limits file loaded. The Watchdog's clock is sim time (`clock=lambda: data.time`), so stops happen at the same frame every run and logs stay deterministic.
   - A latched stop ends the episode as a failure, with reason `watchdog` in the log. The gate run needs zero limit violations.
   - The limits file (`examples/limits/so101-sim.toml`) takes joint ranges from the MJCF `ctrlrange` and says it is for sim only. It is not a validated hardware limits file, and ADR-001 still refuses hardware runs without one.
   - ADR-002's rule stands: no hosted Decider backends on hardware. Jev stays blocked everywhere.
6. **Base install untouched.** `pip install saltmarsh` still pulls in no heavy stack (the existing CI check). New code imports MuJoCo, mink and py_trees only inside the functions that use them.
7. **Logs re-load exactly.** Every log written by the gate run reloads in Python. Setting its qpos and qvel and running `mj_kinematics` reproduces the logged body poses with zero difference in the same build.

### 3. Where it lives

| Piece | Home | Needs |
|---|---|---|
| State-log writer, reader and hashes | `saltmarsh.data.state_log` | standard library only (base install) |
| Asset lock and fetcher | `saltmarsh.simulation.assets`, lock in `src/saltmarsh/simulation/assets/so101.lock.toml` | standard library only |
| Task scene (our MJCF that includes the fetched `so101.xml`), seeded reset, recorder | `saltmarsh.simulation.worlds.so101_pick` | `[arm]` |
| IK helper | `saltmarsh.movement.ik` | `[arm]` |
| Scripted pick-and-place tree | `saltmarsh.behavior.so101_pick` | `[arm]` |
| Success metric and the 50-seed eval | `saltmarsh.eval` (metric, stdlib) and a script under `examples/` | `[arm]` for the episodes |

**A new extra, `[arm]`:** `mujoco==3.15.0`, `mink==1.3.0`, `py_trees==2.6.0`.

- **Why not `[sim]`:** it would put IK and behavior trees into the plain physics extra.
- **Why not `[movement]`:** it pulls in LeRobot and PyTorch (several GB), which the scripted world doesn't need.
- **Why exact pins:** the gate needs them. `[sim]` keeps its range.
- **Changes to ADR-001:** decision 2 gains `[arm]` (it joins `[all]`), and decision 4 gains these exact pins.

### 4. Meshes: fetch on first use from the pinned commit

The SO-101 folder has 19 STL meshes, 18.15 MB in total (26 files and 19.19 MB with the XML, docs and a 1 MB picture).

| Option | Repo growth | Pinning | Cost |
|---|---|---|---|
| Vendor into git | 18 MB in history forever, and more with every model update | implicit | must also be kept out of the sdist |
| Git LFS | small pointers, but files sit in metered LFS storage | implicit | every clone and CI checkout needs `git-lfs` |
| **Fetch on first use, SHA-256 checked** | **none** (one lock file of a few KB) | **explicit: commit + per-file hash** | network on first use |

**Decision: fetch on first use.**

- **The lock file** names the commit and lists every needed file with its size and SHA-256. That covers `so101.xml`, `LICENSE`, `README.md`, `CHANGELOG.md` and `assets/*.stl`, but not the scene files or the picture.
- **Downloads:** files come from `https://raw.githubusercontent.com/google-deepmind/mujoco_menagerie/<commit>/robotstudio_so101/...` into `~/.cache/saltmarsh/menagerie/<commit>/robotstudio_so101/`, or a directory named by `SALTMARSH_ASSETS`.
- **Checks:** each file is written to a temporary name, hashed, then renamed into place. A size or hash mismatch is an error, and the world never loads unverified files. A cached file is re-hashed before use.
- **Offline use:** point `SALTMARSH_ASSETS` at a copy made earlier.
- **CI:** caches the directory, keyed on the lock file's hash.
- **Upstream licence and credit travel with the files:** `LICENSE` and `README.md` are fetched next to the meshes.
- **Our task scene** is a small MJCF of ours that `<include>`s the fetched `so101.xml` and adds the cube, the floor and a goal marker. If any of it is copied from Menagerie's `scene_box.xml`, its SPDX header names that source and its Apache-2.0 licence, and says it was changed.
- **Notices:** `THIRD_PARTY_NOTICES.md` (proposed in #3) gains rows for the SO-101 model and the `[arm]` packages, and `REUSE.toml` covers the lock file. Saltmarsh's own `NOTICE` is unchanged, because we don't redistribute the Menagerie files. The model folder has no `NOTICE` file of its own (checked at the pinned commit).
- **Arena's display meshes** are a separate, decimated set, governed by arena ADR-017.

### 5. The state-log format (`saltmarsh.state-log`, version 1)

**File:** JSON Lines, UTF-8, `\n` line ends, named `<world>-<seed>.state.jsonl`. It can be gzipped for storage or transport (`.state.jsonl.gz`, written with `mtime=0`). Hashes always cover the uncompressed bytes.

- **Line 1, the header:**
  - `kind: "saltmarsh.state-log"` and `version: 1`.
  - `setup`: an object with everything that decides the trajectory:
    - `world: "so101-pick"` and `world_version` (bumped whenever the same seed would play out differently);
    - `seed` (a decimal string);
    - `menagerie_commit`;
    - `scene_hash`, a SHA-256 over the lock file and our scene MJCF;
    - `versions` (mujoco, mink, py_trees, numpy, qpsolvers, daqp, python);
    - `timestep` (0.005 s) and `steps_per_frame` (6, so 30 Hz frames);
    - `task` (start pose, goal, success radius);
    - `policy`, such as `scripted@<git sha>`.
  - `setup_hash`: a SHA-256 of the canonical JSON of `setup` (sorted keys, no spaces).
  - `layout`: `nq`, `nv`, `nmocap`, and body, joint and actuator names in id order.
  - `recorded_on`: OS and CPU, for information only and outside the hash.
- **Lines 2 to N+1, one frame each:**
  - `i` (the frame number) and `t` (sim time).
  - `qpos` and `qvel`.
  - `mocap_pos` and `mocap_quat`, only when `nmocap > 0` (the SO-101 scene has none).
  - `xpos` and `xquat` for every body except the world, in id order. These are the object poses the viewer draws.
  - `ctrl`: the actuator targets used during the frame. It is a record only and is never replayed.
  - `node`: the running behavior-tree node, written only on frames where it changes.
- **Frame timing:**
  - Frame 0 is the state after reset. Frame k is the state after k × 6 physics steps, followed by `mj_kinematics`.
  - The `mj_kinematics` call matters. After `mj_step`, MuJoCo's body poses are one step behind `qpos` (7.8 mm off in a test). Calling it brings them in line, and it leaves the trajectory bit-identical (checked over 900 frames).
- **Last line, the trailer:** `kind: "saltmarsh.state-log.end"`, `frames`, `outcome` (`success`, `reason` such as `placed`, `timeout`, `dropped`, `watchdog` or `unstable`, and the cube's distance to the goal), `final_hash` and `log_hash`.
- **Hashes:**
  - `setup_hash` ties the log to its seed, pins, assets and policy.
  - `final_hash` is a 64-bit FNV-1a over the little-endian IEEE-754 bytes of the last frame's `t`, `qpos`, `qvel` and any mocap values: 16 lowercase hex digits, the same construction as arena's state hash. A reader recomputes it from the parsed last frame, which shows the floats came back bit for bit.
  - `log_hash` is a 64-bit FNV-1a over the bytes of every earlier line, newlines included.
  - FNV-1a instead of ADR-002's SHA-256 keeps the browser reader free of new crates. These hashes catch damage and mismatches; they are not a signature.
- **Numbers:**
  - Floats are float64, written with Python's shortest round-trip form (`json.dumps`, `allow_nan=False`). A NaN or infinity ends the episode as `unstable`.
  - Units are metres, radians and seconds. Quaternions are MuJoCo's (w, x, y, z), and z is up. The viewer converts both for three.js.
- **Why JSONL.** It meets the replay requirement exactly: over 900 frames, qpos read back from JSON matched the recorded values with zero difference, and re-posing from it matched the logged poses with zero difference. Python's `json`, the browser's `JSON.parse` and Rust's `serde_json` all read it with no extra libraries, so the reader fits the base install.

  The size is acceptable. Sizes measured for 30 s at 30 Hz on the SO-101 scene (13 qpos, 12 qvel, 9 bodies):

  | Form | Bytes |
  |---|---|
  | JSONL, full frames | 1,225,418 (438,997 gzipped) |
  | JSONL, qpos and qvel only | 331,863 (124,479 gzipped) |
  | Compressed `.npz`, same data | 361,003 |

  `.npz` would save about 18% over gzipped JSONL, but it needs NumPy (so not the base install) and a zip and `.npy` reader in the browser. Arrow needs `pyarrow` and a large JavaScript library. A binary version 2 can come later if logs grow long.
- **How arena reads it** (arena ADR-017):
  - The page fetches a log, gunzips it if needed (`DecompressionStream`), and hands the text to engine-wasm.
  - engine-wasm checks `kind`, `version`, `log_hash` and `final_hash`, indexes the frames, and returns body poses for the current frame. JavaScript only draws them.
  - A **scene manifest** (`saltmarsh.scene-manifest` v1), exported once per world, gives the page the meshes and their bodies, local poses and colours. It also gives the same `scene_hash`, so a log is never drawn on the wrong scene.
  - Poses on screen are the logged values, held per frame with no interpolation, so playback is exact by construction.
- **Decision logs:** ADR-002's `<log>.decisions.jsonl` works unchanged next to a state log. Its `setup_hash` and `final_hash` refer to the state log instead of an arena replay.

### 6. Licences

| Component | Version | Licence | Notes |
|---|---|---|---|
| MuJoCo | 3.15.0 | Apache-2.0 | |
| mink | 1.3.0 | Apache-2.0 | depends on `qpsolvers[daqp]` |
| qpsolvers | 4.13.0 today | **LGPL-3.0** (its LICENSE and PyPI classifier) | pulled in by mink, already today through `[movement]` |
| daqp | 0.10.3 today | MIT | the QP solver mink uses here |
| py_trees | 2.6.0 | BSD-3-Clause | already pinned for `[gaming]` |
| SO-101 model | Menagerie `f054586a` | Apache-2.0 | derived from The Robot Studio's SO-ARM100 (Apache-2.0) |
| three.js (arena side only) | 0.186.1 | MIT | not a Saltmarsh dependency |

There is no NC, ND or copyleft licence among the assets, and no copyleft licence among the code dependencies except qpsolvers' LGPL.

- We install qpsolvers unmodified from PyPI and don't bundle it, which the LGPL allows.
- Anyone who builds a bundle or container image with it must follow the LGPL, as `THIRD_PARTY_NOTICES.md` already says for FFmpeg.
- ARCHITECTURE.md's "all permissive" line is true of the projects it lists, but not of mink's own dependencies. The notices should name qpsolvers.

### 7. P1 plan: scripted pick in Saltmarsh

The work happens in evenings and on weekends, as always. The finding's estimate is 3–4 sessions.

1. Add the `[arm]` extra, the SO-101 lock file, the fetcher with offline tests (a fake lock, no network), and the provenance card.
2. Add the task scene, the seeded reset and the recorder.
3. Add the mink IK helper, the py_trees tree, the sim limits file and the sim-clock Watchdog.
4. Add `data.state_log`: the writer, the reader and the hashes, with tests for exact round trips, hash checks and clear errors on a wrong kind, version or world.
5. Add the 50-seed eval script, and report the success rate, failures by reason and run time.
6. Add the scene-manifest exporter and three sample logs for arena P2.
7. Add an `arm` job to `docs/ci-spec.md`: install `[arm]`, cache the assets, run the arm tests and a 5-seed smoke run. The workflow change itself goes through whoever owns `.github/`.

**P1 is done when:**
- at least 45 of 50 seeds succeed;
- the gate run has zero Watchdog stops;
- the determinism test passes;
- every log re-loads exactly;
- the base-install check still passes;
- the CI arm job runs in under 2 minutes on Linux.

## Consequences

- Saltmarsh gets its first real world with no change to the base install and no meshes in the repo.
- Logs are bigger than action replays, about 0.44 MB gzipped per 30 s. In return, any reader, in any build or language, sees exactly what MuJoCo computed.
- The first run needs network access to fetch the meshes. After that the cache or `SALTMARSH_ASSETS` is enough.
- Moving MuJoCo, mink, py_trees or the Menagerie commit is a deliberate change to the pins, the lock file and this record. Old logs keep their recorded versions and still play in the viewer, because it reads states.
