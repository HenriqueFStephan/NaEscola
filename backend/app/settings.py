from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "curriculum" / "report.json").exists() and (candidate / "backend").exists():
            return candidate
    raise RuntimeError("Could not locate the NaEscola repository root.")


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    admin_token: str | None
    generation_provider: str | None
    monthly_budget_usd: float | None
    cors_origins: list[str]

    @property
    def curriculum_dir(self) -> Path:
        return self.repo_root / "curriculum"

    @property
    def lessons_dir(self) -> Path:
        return self.repo_root / "content" / "lessons"

    @property
    def maps_dir(self) -> Path:
        return self.repo_root / "content" / "maps" / "mediterranean"

    @property
    def runtime_dir(self) -> Path:
        return self.repo_root / "data" / "runtime"


def load_settings() -> Settings:
    budget = os.environ.get("NAESCOLA_MONTHLY_BUDGET_USD", "").strip()
    origins = os.environ.get(
        "NAESCOLA_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return Settings(
        repo_root=find_repo_root(),
        admin_token=os.environ.get("NAESCOLA_ADMIN_TOKEN") or None,
        generation_provider=os.environ.get("NAESCOLA_GENERATION_PROVIDER") or None,
        monthly_budget_usd=float(budget) if budget else None,
        cors_origins=[item.strip() for item in origins.split(",") if item.strip()],
    )
