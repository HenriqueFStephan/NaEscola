# Project status

Updated 2026-10-28.

## Done

- Grades 3–6 curriculum loaded from the pinned BNCC snapshot: 909 skill placements, 709 distinct codes, 10 general competencies. No duplicate ids, broken links, or prerequisite cycles.
- Official skill statements stay separate from NaEscola's proposed order. Computação is labeled as the 2022 complement. Língua Inglesa is explicitly absent before 6º ano. Ensino Religioso is included and marked as matrícula facultativa.
- FastAPI serves stages, grades, subjects, search, lessons, competencies, and the Mediterranean map snapshots.
- Learner-facing Next.js app, in Brazilian Portuguese, reads those endpoints. Coverage percentages come from published lessons.
- The subject timeline expands and collapses units, filters topics, switches to a list, and shows prerequisite notes.
- Six lessons are published: five from seeded selection `20261028` and the history map for EF06HI13. A seventh lesson, unit fractions, was published by the deterministic packet pipeline.
- The sine graph, number line, array, and map controls were exercised in headless Chrome.
- Berlin days 1–3 are implemented and tested. Monthly generation is **not** operational.

## How to run

API:

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

Web, in another terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. The page calls `http://127.0.0.1:8000`.

Tests:

```bash
cd backend && python3 -m pytest -q
cd apps/web && npm test && npx tsc --noEmit
```

## Not operational

- No language-model provider is configured. Commands without a research packet refuse to invent lesson text.
- `.github/workflows/validation.yml` only runs tests, `window-check`, and `dry-run`. It has not been observed executing on GitHub. It does not publish lessons. Unattended generation on days 1–3 is not operational.
- Agent roles other than the deterministic pipeline are specifications, not autonomous workers.
- Grades 1, 2, 7, 8, and 9, Educação Infantil, Ensino Médio, and Ensino Superior have no curriculum payload.
- State and municipal curricula were not compared one by one.
- Screenshot visual-regression tooling is not set up. Mathematical samples and a headless browser pass are the checks that ran.

## Blocked

The Windows folder is not mounted here. Use the README sync commands. Do not treat an open pull request as merged.
