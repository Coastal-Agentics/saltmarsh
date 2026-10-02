# CI specification

This repository has no workflows yet. This document gives the exact workflow to add as `.github/workflows/ci.yml`. It is a spec only: this repository's workflows are added in separate pull requests.

## Jobs

| Job | Python | What it checks |
|---|---|---|
| `base` | 3.12, 3.13 | `pip install .` pulls in no heavy stack; ruff; the test suite (the MuJoCo test skips) |
| `sim` | 3.12 | `pip install ".[sim]"`; the MuJoCo step test must run and pass headless (`SALTMARSH_REQUIRE_SIM=1` turns a skip into a failure) |
| `all-resolve` | 3.12 | `pip install --dry-run ".[all]"` resolves, so the extras stay installable together |
| `reuse` | 3.12 | `reuse lint` passes (every file has SPDX copyright and license information) |
| `dco` | (none) | pull requests only: every non-merge commit has a `Signed-off-by:` trailer matching its author |

Notes:

- `pip install --group` needs pip 25.1 or newer, so each Python job upgrades pip first.
- The `sim` job does not render, so it needs no display or GL setup. A later rendering test would set `MUJOCO_GL=egl` and install `libegl1`.
- `all-resolve` is a dry run, because a full `[all]` install downloads PyTorch with CUDA libraries (several GB). Add a full install job later if it is needed.
- `dco` compares each commit's `Signed-off-by:` trailers with the commit author, exactly as `git commit -s` writes them.

## `.github/workflows/ci.yml`

```yaml
name: ci

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

jobs:
  base:
    runs-on: ubuntu-24.04
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install (base only)
        run: |
          python -m pip install --upgrade pip
          python -m pip install . --group dev
      - name: Base install pulls in no heavy stack
        run: |
          python - <<'PY'
          import importlib.util, sys
          heavy = ["torch", "mujoco", "gymnasium", "lerobot", "rerun", "open3d", "pettingzoo", "py_trees"]
          found = [m for m in heavy if importlib.util.find_spec(m) is not None]
          print("heavy packages installed:", found)
          sys.exit(1 if found else 0)
          PY
      - name: Lint
        run: |
          ruff check .
          ruff format --check .
      - name: Test
        run: python -m pytest

  sim:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: Install with [sim]
        run: |
          python -m pip install --upgrade pip
          python -m pip install ".[sim]" --group dev
      - name: Test (MuJoCo step must run, not skip)
        env:
          SALTMARSH_REQUIRE_SIM: "1"
        run: python -m pytest

  all-resolve:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: Resolve [all]
        run: |
          python -m pip install --upgrade pip
          python -m pip install --dry-run ".[all]"

  reuse:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
      - name: REUSE lint
        run: |
          python -m pip install --upgrade pip
          python -m pip install --group reuse
          reuse lint

  dco:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - name: Every commit is signed off by its author
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          status=0
          for sha in $(git rev-list --no-merges "$BASE_SHA..$HEAD_SHA"); do
            author="$(git show -s --format='%an <%ae>' "$sha")"
            if git show -s --format='%(trailers:key=Signed-off-by,valueonly)' "$sha" \
                | sed 's/^ *//; s/ *$//' | grep -qxF "$author"; then
              echo "ok      $sha"
            else
              echo "::error::commit $sha has no 'Signed-off-by:' trailer matching its author"
              status=1
            fi
          done
          exit $status
```
