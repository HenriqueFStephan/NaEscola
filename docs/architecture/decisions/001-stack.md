# ADR 001 — Stack

## Status

Accepted.

## Decision

- Frontend: TypeScript, React, Next.js App Router. Learner-facing copy is pt-BR.
- Backend: Python, FastAPI, Pydantic v2. Curriculum, lessons, search, validation, generation, and automation commands stay here.
- Maps and graphs render in the browser from declarative configs. Function plots use an allowlist (`sine`, `linear`, `quadratic`) instead of evaluating lesson-authored expressions.
- Historical boundaries for the first map lesson are a filtered subset of `aourednik/historical-basemaps` at commit `da7a4b735ecef70aebdc9c73e409d8a2500d50f3`, licensed GPL-3.0 for those files only. Strokes stay marked as approximate because the upstream `BORDERPRECISION` is 1. No intermediate borders are generated.

## Consequences

Two processes run in development: Uvicorn on port 8000 and Next.js on port 3000. The browser talks to the API with `NEXT_PUBLIC_API_URL`.
