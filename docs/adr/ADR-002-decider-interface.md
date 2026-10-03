# ADR-002: The Decider interface

- **Status:** Proposed
- **Date:** 2026-10-03

## Context

Some agent and eval logic needs fuzzy, typed judgments that hand-written rules handle badly: "which target now?", "was this match a stalemate?", "is this user-written text acceptable?". Arena [ADR-015](https://github.com/starscream-agentics/arena/blob/main/docs/DECISIONS.md) (Accepted, 2026-10-03) allows TypeSafe AI's hosted Jev model for exactly this, outside the 60 Hz tick, with every decision logged, and puts the interface for it in Saltmarsh. This record fixes that interface. It adds no code and no dependencies.

## Decisions

1. **One small interface, `Decider`.** It takes a state as text plus typed questions and returns typed answers. It is a protocol, not a framework. A sketch (not code in the package):

   ```python
   # Sketch only.
   Question = Choice(name, options) | Score(name, levels) | Truth(name)  # Truth is a 0-1 value (Jev calls it Noul)
   Answer   = (name, value, probabilities or None)

   class Decider(Protocol):
       name: str        # e.g. "py_trees", "log", "outlines", "jev"
       version: str     # library or model version, pinned (e.g. "jev-1.13.0", never an alias)
       def decide(self, state: str, questions: Sequence[Question]) -> Decision: ...

   # Decision = answers + backend name + backend version + request_hash
   ```

   - `request_hash` is a SHA-256 of the canonical JSON of the state and the questions.
   - The state is rendered to text by deterministic code. Numbers become words where a backend reads numbers badly ("enemy 2: close, low HP").

2. **Where it sits.**
   - The interface, its types and the `log` backend live in `behavior` (`saltmarsh.behavior.decider`), since a Decider is part of a policy. They use only the standard library, so they work on the base install.
   - `gaming` runs the slow "strategist": every N ticks it asks a Decider for a mode or target, and a deterministic controller turns that into actions on every tick. Headless matches run in lockstep: the harness waits for the answer between ticks, so the sim never sees the clock.
   - Replay scoring and guardrails run in `behavior` or `gaming` and hand plain results to `eval`. `eval` never imports a Decider, so ADR-001's rule that `data` and `eval` depend on no other part still holds.

3. **Backends.**

   | Backend | Needs | Extra | Status |
   |---|---|---|---|
   | `py_trees` behavior tree | nothing hosted, no key | `[gaming]` (py_trees already pinned) | **Default** |
   | `log`: plays back a decision log | the log file | base | For CI and replays |
   | Outlines, vLLM or llguidance with a local model | a local model; its license must pass the `data` license gate | a new extra, later | Local option |
   | Jev (TypeSafe AI, hosted) | a company API key | a new extra, later | **Blocked** |

   - **Jev is blocked** until Coastal Agentics, not any individual, holds the account. That waits for the company to be formed and for the company's attorney to review TypeSafe's terms. Until then there is no Jev dependency, no key and no API call anywhere.
   - No extra is added by this record. Each new extra comes with the PR that adds its backend.
   - Saltmarsh, its tests and CI never need an API key.

4. **The decision log.** A separate file next to the arena replay, `<replay>.decisions.jsonl`, one JSON object per line:
   - **Header** (first line): `kind: "saltmarsh.decision-log"`, `version: 1`, and the arena replay's `setup_hash`. That hash is known when the match starts.
   - **One line per decision:** `tick` (the tick the answer applies to), `agent`, `request_hash`, `backend`, `backend_version`, the request (state text and questions), the answers, and `latency_ms`.
   - **Trailer** (last line): the arena replay's `final_hash`, the number of decisions, and `log_hash`, a SHA-256 over every earlier line's bytes.
   - **Checks:** the `setup_hash` and `final_hash` must match the replay, and `log_hash` must match the file. Replaying the controller with the `log` backend must regenerate the replay's per-tick actions. If a request hash differs from the log at the same point, the policy has diverged, and the `log` backend fails rather than guessing.
   - The arena replay alone still re-simulates the match, because it stores actions. The log makes the decisions behind those actions checkable. Putting the log inside the replay would be an arena replay-format change, and it is not proposed.

5. **Safety is unchanged.** `run_eval` still calls `check_safety` before the first episode, and there is still no way to skip it. A Decider never sends commands itself: its answers go to a controller, and every command still goes through `Watchdog.guard` and the robot's limits. Hosted backends are not used on hardware runs.

6. **Never a training source for imitation or distillation.** TypeSafe's [Master Customer Agreement](https://typesafe.ai/legal/mca), section 2.3(b), forbids using the Services or Output "to perform model distillation, train a model to imitate the output of the Services, or develop (or to facilitate the development of) a similar or competing product or service".
   - No policy, dataset or model of ours is trained on Jev output.
   - Logs from the `jev` backend are never exported as training data, and a provenance card records which backend made each decision.
   - **Using Jev scores as an RL reward or an evolution fitness is not allowed** until the company's attorney clears it.
   - Published baselines never depend on Jev.

## Consequences

- Saltmarsh core stays open, local and key-free. A behavior tree or a log is always enough to run a match, a test or a replay.
- Any backend can be swapped for another with the same questions, so results do not depend on one vendor.
- Decision logs make runs that use a non-deterministic backend reproducible and auditable, at the cost of one more file per match.

## Open questions

1. Is `saltmarsh.behavior.decider` the right home, or should Deciders be their own module outside the seven parts?
2. Should the log keep the full state text for each decision (self-checking, larger) or only its hash (smaller, but harder to audit)?
3. Names for the later extras, for example `[decider-local]` and `[typesafe]`?
