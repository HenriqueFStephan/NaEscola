import json
from pathlib import Path

from app.main import app
from app.services.graph import broken_references, duplicate_topic_ids, find_cycles

ROOT = Path(__file__).resolve().parents[2]


def test_grades_3_to_6_keep_their_skills_and_edges():
    baseline = json.loads((ROOT / "curriculum/baseline-grades-3-6.json").read_text(encoding="utf-8"))
    catalog = app.state.catalog
    for grade, expected in baseline["grades"].items():
        document = json.loads((ROOT / "curriculum" / f"grade-{grade}.json").read_text(encoding="utf-8"))
        assert [subject["id"] for subject in document["subjects"]] == expected["subjectIds"]
        assert document["omissions"] == expected["omissions"]
        actual = [topic for subject in document["subjects"] for unit in subject["units"] for topic in unit["topics"]]
        assert len(actual) == len(expected["topics"])
        for topic, old in zip(actual, expected["topics"]):
            assert topic["id"] == old["id"]
            assert topic["summary"] == old["text"]
            assert topic["proposedOrder"] == old["proposedOrder"]
            assert topic["sequenceBasis"] == old["sequenceBasis"]
            assert topic["complexity"] == old["complexity"]
            assert topic["lessonTypes"] == old["lessonTypes"]
            assert topic["suggestedVisualizations"] == old["suggestedVisualizations"]
            assert topic["relatedTopicIds"] == old["relatedTopicIds"]
            conceptual = [item["topicId"] for item in topic["prerequisites"] if item["kind"] == "conceptual"]
            cross = [item["topicId"] for item in topic["prerequisites"] if item["kind"] == "cross-subject"]
            continuity = [item["topicId"] for item in topic["prerequisites"] if item["kind"] == "same-official-code-previous-year"]
            assert set(old["conceptual"]) <= set(conceptual)
            assert cross == old["cross"]
            assert set(old["continuity"]) <= set(continuity)
            assert catalog.topic(topic["id"]) is not None


def test_new_segments_follow_the_official_cut():
    catalog = app.state.catalog
    assert catalog.grades["ei-bebes"].segmentKind == "grupo-etario"
    assert catalog.grades["ei-bebes"].skillPlacement == "official-age-group"
    assert any(subject.codeSigla == "CO" for subject in catalog.grades["ei-pequenas"].subjects)
    assert all(subject.codeSigla != "CO" for subject in catalog.grades["ei-bebes"].subjects)
    babies = catalog.topic("ei-bebes-ei01cg01")["topic"]
    assert babies.objectiveOrigin == "official-learning-objective"
    assert "Movimentar as partes do corpo" in babies.summary
    later = catalog.topic("ei-bem-pequenas-ei02cg01")["topic"]
    assert "ei-bebes-ei01cg01" in {item.topicId for item in later.prerequisites}

    stage = catalog.grades["em-etapa"]
    assert stage.skillPlacement == "stage-not-a-year"
    assert stage.gradeNumber == 0
    sample = catalog.topic("em-etapa-em13chs101")["topic"]
    assert sample.skills[0].officialYears == []
    assert "sem-seriacao-oficial" in sample.flags
    assert "Identificar, analisar e comparar diferentes fontes" in sample.summary
    for series_id in ("em-1", "em-2", "em-3"):
        series = catalog.grades[series_id]
        assert series.skillPlacement == "series-has-no-official-skills"
        assert series.officialSkillCatalogId == "em-etapa"
        assert all(not unit.topics for subject in series.subjects for unit in subject.units)
    religion = next(item for item in stage.omissions if item.component == "Ensino Religioso")
    assert "210" in religion.reason
    english = next(subject for subject in catalog.grades["ef-7"].subjects if subject.codeSigla == "LI")
    assert english.officialStatus == "bncc-2018"
    assert all(subject.codeSigla != "LI" for subject in catalog.grades["ef-1"].subjects)
    assert "ensino-superior" not in catalog.grades
    assert find_cycles(catalog) == []
    assert broken_references(catalog) == []
    assert duplicate_topic_ids(catalog) == []


def test_raw_files_have_unique_ids_and_closed_references():
    curriculum = ROOT / "curriculum"
    seen: set[str] = set()
    duplicates: list[str] = []
    known: set[str] = set()
    links: list[tuple[str, str]] = []
    for path in sorted(curriculum.glob("*.json")):
        if path.name in {"competencies.json", "report.json", "baseline-grades-3-6.json"}:
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        for key in (document["gradeId"],):
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        for subject in document["subjects"]:
            if subject["id"] in seen:
                duplicates.append(subject["id"])
            seen.add(subject["id"])
            for unit in subject["units"]:
                if unit["id"] in seen:
                    duplicates.append(unit["id"])
                seen.add(unit["id"])
                for topic in unit["topics"]:
                    if topic["id"] in seen:
                        duplicates.append(topic["id"])
                    seen.add(topic["id"])
                    known.add(topic["id"])
                    for link in topic["prerequisites"]:
                        links.append((topic["id"], link["topicId"]))
                    for related in topic["relatedTopicIds"]:
                        links.append((topic["id"], related))
    assert duplicates == []
    assert [source for source, target in links if target not in known] == []
