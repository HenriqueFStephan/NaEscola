# NaEscola

NaEscola organizes school knowledge as a sequence of topics, skills, and lessons. This version loads the Brazilian BNCC for the 3º, 4º, 5º, and 6º anos of Ensino Fundamental, and keeps that official text separate from NaEscola's proposed teaching order.

The Windows folder below is **not** where this repository was built. These commands are for syncing a local checkout with GitHub.

## Sync with the Windows folder

If the folder does not exist yet, in PowerShell or Command Prompt:

```bat
cd /d "C:\Users\henri\OneDrive\Área de Trabalho\Leisure\VSC"
git clone https://github.com/HenriqueFStephan/NaEscola.git
cd /d "C:\Users\henri\OneDrive\Área de Trabalho\Leisure\VSC\NaEscola"
```

If the folder already exists:

```bat
cd /d "C:\Users\henri\OneDrive\Área de Trabalho\Leisure\VSC\NaEscola"
git status
git remote -v
git fetch origin
git switch main
git pull origin main
```

To review a pull request branch without merging it:

```bat
git fetch origin
git switch <branch-name>
```

Do not copy files over the folder by hand. Pull the branch you want. If `git status` shows local work, commit or stash it before switching branches.

## API

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs`.

Environment variables are listed in `.env.example`. Leave `NAESCOLA_GENERATION_PROVIDER` empty unless a real provider is configured. Monthly unattended generation is not operational.

## Tests

```bash
cd backend
python3 -m pytest -q
```

Curriculum checks:

```bash
python3 -m app.automation.cli validate
python3 -m app.automation.cli dry-run
python3 -m app.automation.cli window-check
```

Run those three from the `backend` directory, or set `PYTHONPATH`.

## Curriculum

`scripts/build_curriculum.py` reads `data/sources/` and writes `curriculum/grade-3.json` through `grade-6.json`, `curriculum/competencies.json`, and the Markdown in `docs/curriculum/`. Human-readable notes on what is official and what is proposed are in `docs/curriculum/overview.md`.

## Layout

- `backend/` — FastAPI application and tests.
- `curriculum/` — generated curriculum.
- `data/sources/` — pinned BNCC snapshot and attribution.
- `content/maps/mediterranean/` — approximate historical GeoJSON and its GPL-3.0 notice.
- `docs/` — architecture, status, and curriculum notes.

## Contributing

Work on a branch. Open a pull request. Do not treat an open pull request as merged.

Keep learner-facing text in Brazilian Portuguese. Keep code and technical docs in English. Do not invent BNCC codes, sources, or territorial polygons. A lesson that fails validation stays unpublished.

## License

The repository owner has not chosen a project-wide license. Curriculum compilation data is CC BY 4.0 as attributed in `data/sources/ATTRIBUTION.md`. The Mediterranean GeoJSON files are under GPL-3.0; see `content/maps/mediterranean/DATA-LICENSE.md`.
