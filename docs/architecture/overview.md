# Architecture

NaEscola is a monorepo. The FastAPI service in `backend/` owns curriculum reading, search, lesson publication rules, generation tasks, and the Berlin calendar window. The Next.js app in `apps/web/` renders Brazilian Portuguese pages and calls that API. It does not decide whether a lesson can be published.

Curriculum JSON in `curriculum/` is generated from the pinned BNCC snapshot by `scripts/build_curriculum.py`. Lessons live in `content/lessons/` as validated JSON. Interactive blocks name a trusted component and a checked config. Lesson files do not contain executable code.

Persistence is JSON files behind `CurriculumCatalog`, `LessonStore`, and `TaskStore`. Those stores are the seam for a later database. See `docs/architecture/mongodb.md`.

Official BNCC codes and wording stay distinct from NaEscola's proposed order, complexity estimates, and prerequisite links. A lesson whose validation report is not publishable is saved as `needs_revision` or left unpublished. The public lesson route only returns `published`.
