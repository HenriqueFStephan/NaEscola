# Project status

Updated 2026-10-28.

## Done in this tree

- Repository inspected. It contained only the initial commit on `main`.
- FastAPI app loads the grades 3–6 curriculum, searches it, and refuses unauthenticated generation.
- Curriculum build from the pinned BNCC snapshot: 909 skill placements, 709 distinct codes, 10 general competencies, no duplicate ids, no broken prerequisite links, no cycles.
- Official wording is separate from the proposed sequence. See `docs/architecture/decisions/003-bncc-sequence.md`.
- Publication gate: invalid BNCC codes, missing references, missing review, and rejected reviews do not remain `published`.
- Map snapshots for six documented years are filtered from historical-basemaps. Borders stay marked approximate. No interpolated years.
- Berlin days 1–3 are implemented and tested, including winter and summer time. Monthly generation is **not** operational.

## Not done yet

- Learner-facing Next.js interface.
- The six initial lessons and the pipeline-published lesson.
- Agent specification files and the GitHub Actions workflow file.

## How to run the API

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

Tests:

```bash
cd backend
python3 -m pytest -q
```

Rebuild the curriculum after a source update:

```bash
python3 scripts/build_curriculum.py
```

## Blocked

- The Windows folder `C:\Users\henri\OneDrive\Área de Trabalho\Leisure\VSC\NaEscola` is not mounted here. Sync commands are in the README.
- No generation-provider credential and no verified live scheduler. Unattended monthly lesson generation must not be described as running.
