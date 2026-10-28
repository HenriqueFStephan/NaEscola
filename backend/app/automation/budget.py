from __future__ import annotations

import json
from pathlib import Path


class BudgetManager:
    """Tracks known costs. It does not invent token usage."""

    def __init__(self, path: Path, monthly_budget_usd: float | None) -> None:
        self.path = path
        self.monthly_budget_usd = monthly_budget_usd

    def load(self) -> dict:
        if not self.path.exists():
            return {"knownCostUsd": 0.0, "entries": [], "unknownUsageEvents": 0}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def can_start(self) -> tuple[bool, str]:
        if self.monthly_budget_usd is None:
            return False, "No monthly budget is configured. The runner will not assume an unlimited budget."
        ledger = self.load()
        if ledger["unknownUsageEvents"]:
            return False, "A previous task did not report usage. New tasks stay stopped."
        if ledger["knownCostUsd"] >= self.monthly_budget_usd:
            return False, "Known cost has reached the configured budget."
        return True, "Budget available for a task with a known cost."

    def record(self, *, task_id: str, cost_usd: float | None) -> None:
        ledger = self.load()
        if cost_usd is None:
            ledger["unknownUsageEvents"] += 1
            ledger["entries"].append({"taskId": task_id, "costUsd": None})
        else:
            ledger["knownCostUsd"] = round(ledger["knownCostUsd"] + cost_usd, 6)
            ledger["entries"].append({"taskId": task_id, "costUsd": cost_usd})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
