from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.graph import broken_references, find_cycles

ROOT = Path(__file__).resolve().parents[2]


def test_catalog_matches_official_counts():
    catalog = app.state.catalog
    assert set(catalog.grades) == {"ef-3", "ef-4", "ef-5", "ef-6"}
    assert len(catalog.topics) == catalog.report["placements"] == 909
    assert catalog.report["uniqueSkills"] == 709
    assert find_cycles(catalog) == []
    assert broken_references(catalog) == []
    assert catalog.competencies["general"]
    assert len(catalog.competencies["general"]) == 10


def test_distinguishes_official_skills_from_proposed_sequence():
    topic = app.state.catalog.topic("ef-3-ma-ef03ma01")["topic"]
    assert topic.objectiveOrigin == "official-skill-statement"
    assert topic.sequenceKind == "naescola-proposed"
    assert "BNCC não define" in topic.sequenceBasis or "não" in topic.sequenceBasis
    assert topic.bnccSkillCodes == ["EF03MA01"]
    assert "números naturais" in topic.summary


def test_english_starts_at_grade_6_and_religion_is_flagged():
    grade3 = app.state.catalog.grades["ef-3"]
    assert any(item.component == "Língua Inglesa" for item in grade3.omissions)
    assert all(subject.codeSigla != "LI" for subject in grade3.subjects)
    grade6 = app.state.catalog.grades["ef-6"]
    assert any(subject.codeSigla == "LI" for subject in grade6.subjects)
    religion = next(subject for subject in grade3.subjects if subject.codeSigla == "ER")
    assert religion.localDependencyNote
    assert any("matricula-facultativa" in topic.flags for unit in religion.units for topic in unit.topics)
    computing = next(subject for subject in grade6.subjects if subject.codeSigla == "CO")
    assert computing.officialStatus == "complemento-computacao-2022"


def test_fraction_chain_is_cross_grade():
    equivalent = app.state.catalog.topic("ef-5-ma-ef05ma04")["topic"]
    targets = {item.topicId for item in equivalent.prerequisites}
    assert "ef-5-ma-ef05ma03" in targets
    operations = app.state.catalog.topic("ef-6-ma-ef06ma10")["topic"]
    assert "ef-6-ma-ef06ma07" in {item.topicId for item in operations.prerequisites}


def test_every_code_exists_in_the_pinned_source():
    import json

    fundamental = json.loads((ROOT / "data/sources/bncc-2018/ensino-fundamental.json").read_text(encoding="utf-8"))
    computing = json.loads((ROOT / "data/sources/computacao-2022/computacao.json").read_text(encoding="utf-8"))
    official = {item["codigo"] for item in fundamental["habilidades"]}
    official.update(item["codigo"] for item in computing["habilidades_ef"])
    used = set()
    for record in app.state.catalog.iter_topics():
        used.update(record["topic"].bnccSkillCodes)
    assert used <= official
    expected = set()
    for item in fundamental["habilidades"]:
        if any(year in {3, 4, 5, 6} for year in item["anos"]):
            expected.add(item["codigo"])
    for item in computing["habilidades_ef"]:
        if any(year in {3, 4, 5, 6} for year in item["anos"]):
            expected.add(item["codigo"])
    assert used == expected


def test_api_navigation_uses_stored_counts():
    client = TestClient(app)
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["topics"] == 909
    assert health.json()["monthlyAutomationOperational"] is False
    grade = client.get("/api/grades/ef-4").json()
    assert grade["status"] == "curriculum_loaded"
    assert grade["topicCount"] == 203
    assert grade["coveragePercent"] == 0 or grade["publishedLessonCount"] <= grade["topicCount"]
    missing = client.get("/api/grades/ef-2").json()
    assert missing["status"] == "not_researched"
    assert missing["publishedLessonCount"] == 0
    subject_id = grade["subjects"][0]["id"]
    subject = client.get(f"/api/grades/ef-4/subjects/{subject_id}")
    assert subject.status_code == 200
    assert subject.json()["sequenceNote"]
    search = client.get("/api/search", params={"q": "frações"})
    assert search.status_code == 200
    assert search.json()["topics"]
