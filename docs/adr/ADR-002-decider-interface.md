# ADR-002: The Decider interface

- **Status:** Accepted
- **Date:** 2026-10-03

## Context

Some agent and eval logic needs fuzzy, typed judgments that hand-written rules handle badly: "which target now?", "was this match a stalemate?", "is this user-written text acceptable?". Arena [ADR-015](https://github.com/starscream-agentics/arena/blob/main/docs/DECISIONS.md) (Accepted, 2026-10-03) allows TypeSafe AI's hosted Jev model for exactly this, outside the 60 Hz tick, with every decision logged, and puts the interface for it in Saltmarsh. This record fixes that interface. It was accepted on review of PR #2, which answered its open questions; those answers are recorded below as decisions. It adds no code and no dependencies.

## Decisions

1. **One small interface, `Decider`.** It takes a state as text plus typed questions and returns typed answers. It is a protocol, not a framework. A sketch (not code in the package):

   ```python
   # Sketch only. Truth is a 0-1 value (Jev calls it Noul).
   Question = Choice(name, options) | Score(name, levels) | Truth(name)
   Answer = (name, value, probabilities or None)


   class Decider(Protocol):
       name: str  # e.g. "py_trees", "log", "outlines", "jev"
       version: str  # pinned library or model version, e.g. "jev-1.13.0", never an alias

       def decide(self, state: str, questions: Sequence[Question]) -> Decision: ...


   # Decision = answers + backend name + backend version + request_hash
   ```

   - `request_hash` is a SHA-256 of the canonical JSON of the state and the questions.
   - The state is rendered to text by deterministic code. Numbers become words where a backend reads numbers badly ("enemy 2: close, low HP").

2. **Where it sits.**
   - **Home: `saltmarsh.behavior.decider`.** The interface, its types and the `log` backend live there, since a Decider is part of a policy. They use only the standard library, so they work on the base install.
   - `gaming` runs the slow "strategist": every N ticks it asks a Decider for a mode or target, and a deterministic controller turns that into actions on every tick. Headless matches run in lockstep: the harness waits for the answer between ticks, so the sim never sees the clock.
   - Replay scoring and guardrails run in `behavior` or `gaming` and hand plain results to `eval`. `eval` never imports a Decider, so ADR-001's rule that `data` and `eval` depend on no other part still holds.

3. **Backends.**

   | Backend | Needs | Extra | Status |
   |---|---|---|---|
   | `py_trees` behavior tree | nothing hosted, no key | `[gaming]` (py_trees already pinned) | **Default** |
   | `log`: plays back a decision log | the log file | base | For CI and replays |
   | Outlines with a local model | a local model; its license must pass the `data` license gate | `[decider-outlines]` | Local option |
   | vLLM, self-hosted | a local model, as above | `[decider-vllm]` | Local option |
   | llguidance with a local model | a local model, as above | `[decider-llguidance]` | Local option |
   | Jev (TypeSafe AI, hosted) | a company API key | `[decider-jev]`, **not in `[all]`** | **Blocked** |

   - **Jev is blocked** until Coastal Agentics, not any individual, holds the account. That waits for the company to be formed and for the company's attorney to review TypeSafe's terms. Until then there is no Jev dependency, no key and no API call anywhere.
   - **Extras are named after their backend.** This record only names them; none is added to `pyproject.toml` yet. Each one lands with the PR that adds its backend. `[decider-jev]` stays out of `[all]` until the company account exists.
   - Saltmarsh, its tests and CI never need an API key.

4. **The decision log.** A separate file next to the arena replay, `<replay>.decisions.jsonl`, one JSON object per line:
   - **Header** (first line): `kind: "saltmarsh.decision-log"`, `version: 1`, and the arena replay's `setup_hash`. That hash is known when the match starts.
   - **One line per decision:** `tick` (the tick the answer applies to), `agent`, `request_hash`, `backend`, `backend_version`, the request (state text and questions), the answers, and `latency_ms`.
   - **Full state text by default.** Sim state is ours, and audits need it.
   - **Hash-only option, `hash_only`,** for anything sensitive. The header records `state: "hash"` instead of `state: "full"`, and each line drops the state text and keeps everything else, including `request_hash`. The `log` backend still recomputes the request hash from the state the controller builds on playback and fails on a mismatch. What is lost is reading or re-asking the exact state from the log alone.
   - **Trailer** (last line): the arena replay's `final_hash`, the number of decisions, and `log_hash`, a SHA-256 over every earlier line's bytes.
   - **Checks:** the `setup_hash` and `final_hash` must match the replay, and `log_hash` must match the file. Replaying the controller with the `log` backend must regenerate the replay's per-tick actions. If a request hash differs from the log at the same point, the policy has diverged, and the `log` backend fails rather than guessing.
   - The arena replay alone still re-simulates the match, because it stores actions. The log makes the decisions behind those actions checkable. Putting the log inside the replay would be an arena replay-format change, and it is not proposed.

5. **Safety is unchanged.** `run_eval` still calls `check_safety` before the first episode, and there is still no way to skip it. A Decider never sends commands itself: its answers go to a controller, and every command still goes through `Watchdog.guard` and the robot's limits. **Rule: no hosted backends on hardware runs.** Only `py_trees`, `log` and local backends may be used when the run target is hardware.

6. **Never a training source for imitation or distillation.** TypeSafe's [Master Customer Agreement](https://typesafe.ai/legal/mca), section 2.3(b), forbids using the Services or Output "to perform model distillation, train a model to imitate the output of the Services, or develop (or to facilitate the development of) a similar or competing product or service".
   - No policy, dataset or model of ours is trained on Jev output.
   - Logs from the `jev` backend are never exported as training data, and a provenance card records which backend made each decision.
   - **Using Jev scores as an RL reward or an evolution fitness is not allowed** until the company's attorney clears it.
   - Published baselines never depend on Jev.

## Consequences

- Saltmarsh core stays open, local and key-free. A behavior tree or a log is always enough to run a match, a test or a replay.
- Any backend can be swapped for another with the same questions, so results do not depend on one vendor.
- Decision logs make runs that use a non-deterministic backend reproducible and auditable, at the cost of one more file per match.
