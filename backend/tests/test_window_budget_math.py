from datetime import datetime, timezone
from pathlib import Path

import math
import pytest

from app.automation.budget import BudgetManager
from app.automation.window import in_generation_window
from app.services.plot_math import evaluate


def test_berlin_window_respects_winter_and_summer_time():
    assert in_generation_window(datetime(2026, 1, 1, 23, 30, tzinfo=timezone.utc))
    assert in_generation_window(datetime(2026, 7, 2, 22, 30, tzinfo=timezone.utc))
    assert not in_generation_window(datetime(2026, 7, 3, 22, 30, tzinfo=timezone.utc))
    assert in_generation_window(datetime(2026, 3, 1, 23, 30, tzinfo=timezone.utc))
    assert not in_generation_window(datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc))


def test_budget_stops_without_configuration_or_unknown_usage(tmp_path: Path):
    manager = BudgetManager(tmp_path / "budget.json", None)
    allowed, _reason = manager.can_start()
    assert allowed is False
    configured = BudgetManager(tmp_path / "budget.json", 2.0)
    configured.record(task_id="a", cost_usd=None)
    allowed, reason = configured.can_start()
    assert allowed is False
    assert "usage" in reason.lower() or "report" in reason.lower()


def test_sine_identity_and_linear_quadratic():
    assert evaluate("sine", {"A": 2, "B": 1, "C": 0, "D": 0}, math.pi / 2) == pytest.approx(2)
    assert evaluate("sine", {"A": 1, "B": 1, "C": 0, "D": 3}, 0) == pytest.approx(3)
    assert evaluate("linear", {"A": 2, "B": -1}, 4) == 7
    assert evaluate("quadratic", {"A": 1, "B": 0, "C": -1}, 3) == 8


def test_map_snapshots_are_approximate_and_named():
    root = Path(__file__).resolve().parents[2] / "content/maps/mediterranean"
    manifest = json_load(root / "manifest.json")
    assert [item["id"] for item in manifest["states"]] == ["bc323", "bc200", "bc100", "ce100", "ce200", "ce400"]
    expectations = {
        "bc323": "Rome",
        "bc100": "Roman Republic",
        "ce100": "Roman Empire",
        "ce400": "Western Roman Empire",
    }
    for state_id, name in expectations.items():
        document = json_load(root / f"{state_id}.geojson")
        names = {feature["properties"]["name"] for feature in document["features"]}
        precisions = {feature["properties"]["borderPrecision"] for feature in document["features"]}
        assert name in names
        assert precisions == {1}
        assert "interpolat" in document["naescola"]["inclusionRule"].lower() or "No border was interpolated" in document["naescola"]["inclusionRule"]


def json_load(path: Path):
    import json

    return json.loads(path.read_text(encoding="utf-8"))
