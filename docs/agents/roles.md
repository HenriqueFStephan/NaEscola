# Agent roles

Updated 2026-10-28.

Only the deterministic pipeline in `backend/app/generation/pipeline.py` runs. It accepts a research packet, locks the topic, validates the lesson, and publishes only when the gate passes. It does not call a language model. Running it twice with the same packet is idempotent. A failing packet is stored as `needs_revision` and is not served by the public lesson route.

The other roles below are instruction boundaries for later work. They are not autonomous workers, and they were not executed as separate agents in this repository.

| Role | State | Boundary |
| --- | --- | --- |
| Curriculum research | Specification | Use the pinned BNCC snapshot. Do not invent codes. |
| Instructional design | Specification | Choose representations for the concept. Do not claim a learning-style taxonomy. |
| Subject specialists | Specification | One subject at a time. Stay inside the cited sources. |
| Text and explanation | Specification | Write original pt-BR explanations. Do not copy textbooks. |
| Mathematical visualization | Partial | The allowlisted plot, number line, and array grid exist and are tested. The role is not a separate worker. |
| Geographic and historical visualization | Partial | The Mediterranean map renders documented snapshots only. The role is not a separate worker. |
| Scientific simulation | Planned | No simulation library beyond the state-step component. |
| Assessment | Partial | Knowledge checks ship explanatory feedback. They are not secure exams. |
| Fact-checking | Partial | Deterministic checks reject bad codes, missing references, and rejected reviews. There is no independent fact-checking worker that can be described as having reviewed the prose. |
| UI and accessibility | Partial | The interface has keyboard controls, list view, focus outlines, and reduced-motion handling. No separate accessibility agent ran. |
| Quality assurance | Partial | Pytest, Vitest, and one headless Chrome pass ran. There is no standing QA worker. |
| Orchestrator | Partial | Task states, locks, and the generation report exist. The orchestrator does not schedule other agents. |

## Handoff

A later worker should read `docs/PROJECT_STATUS.md`, `curriculum/report.json`, and `content/reports/`. Do not republish a topic that already has a published lesson. Do not mark a role implemented unless a command in this repository actually performs it.
