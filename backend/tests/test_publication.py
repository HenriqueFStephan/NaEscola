import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.generation.pipeline import run_packet
from app.main import app
from app.persistence.catalog import LessonStore, TaskStore
from app.schemas.content import Lesson
from app.services.validation import validate_lesson


def lesson_body(status: str = "published", code: str = "EF03MA01", **overrides) -> dict:
    record = app.state.catalog.topic("ef-3-ma-ef03ma01")
    payload = {
        "id": "lesson-ef03ma01-test",
        "slug": "teste-numeros-naturais",
        "title": "Números até o milhar",
        "language": "pt-BR",
        "gradeId": record["grade"].gradeId,
        "subjectId": record["subject"].id,
        "unitId": record["unit"].id,
        "topicId": record["topic"].id,
        "learningObjectives": [record["topic"].learningObjectives[0]],
        "bnccSkillCodes": [code],
        "prerequisiteLessonIds": [],
        "blocks": [
            {"type": "heading", "level": 2, "text": "O que vamos aprender"},
            {"type": "paragraph", "text": "Um número natural pode ser lido em algarismos e em palavras."},
            {
                "type": "visualization",
                "component": "number-line",
                "title": "Reta até 10",
                "description": "Uma reta numerada de 0 a 10.",
                "config": {
                    "min": 0,
                    "max": 10,
                    "step": 1,
                    "ticks": [0, 5, 10],
                    "markers": [{"value": 4, "label": "4"}],
                    "initial": 4,
                },
            },
            {
                "type": "knowledge-check",
                "id": "check-1",
                "prompt": "Qual número vem logo depois de 999?",
                "choices": [
                    {"id": "a", "text": "1000"},
                    {"id": "b", "text": "990"},
                ],
                "correctChoiceId": "a",
                "feedbackCorrect": "Depois de 999 vem 1000, que é a unidade de milhar.",
                "feedbackIncorrect": "990 é menor do que 999. O próximo número é 1000.",
            },
            {"type": "summary", "points": ["999 é o maior número de três algarismos.", "1000 abre a ordem do milhar."]},
        ],
        "references": [
            {
                "id": "bncc",
                "title": "Base Nacional Comum Curricular",
                "authorOrInstitution": "Ministério da Educação",
                "url": "https://basenacionalcomum.mec.gov.br/images/BNCC_EI_EF_110518_versaofinal_site.pdf",
                "identifier": "EF03MA01",
                "publicationDate": "2017-12-22",
                "accessedAt": "2026-10-28",
                "sourceType": "official-curriculum",
                "relevantClaims": ["Habilidade EF03MA01."],
            }
        ],
        "status": status,
        "version": 1,
        "createdAt": "2026-10-28T00:00:00+00:00",
        "updatedAt": "2026-10-28T00:00:00+00:00",
        "sequenceNote": "Sequência proposta pela NaEscola, não ordem obrigatória da BNCC.",
        "uncertaintyNotes": [],
        "reviews": [
            {
                "id": "review-1",
                "method": "deterministic-schema-source-and-curriculum-gates",
                "decision": "approve",
                "notes": "Conferidos código, enunciado e referência.",
                "createdAt": "2026-10-28T00:00:00+00:00",
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_invalid_bncc_code_is_not_publishable(tmp_path: Path):
    body = lesson_body(code="EF99MA99")
    lesson = Lesson.model_validate(body)
    report = validate_lesson(lesson, app.state.catalog, LessonStore(tmp_path))
    assert report.publishable is False
    assert any(issue.code == "bncc" for issue in report.issues)


def test_rejected_review_blocks_publication(tmp_path: Path):
    body = lesson_body()
    body["reviews"] = [
        {
            "id": "review-reject",
            "method": "source-check",
            "decision": "reject",
            "notes": "Referência insuficiente.",
            "createdAt": "2026-10-28T00:00:00+00:00",
        }
    ]
    lesson = Lesson.model_validate(body)
    report = validate_lesson(lesson, app.state.catalog, LessonStore(tmp_path))
    assert report.publishable is False


def test_pipeline_does_not_publish_a_failing_packet(tmp_path: Path):
    lessons = LessonStore(tmp_path / "lessons")
    tasks = TaskStore(tmp_path / "runtime")
    body = lesson_body(code="EF99MA99")
    result = run_packet(
        {"topicId": "ef-3-ma-ef03ma01", "lesson": body},
        catalog=app.state.catalog,
        lessons=lessons,
        tasks=tasks,
        provider_configured=False,
    )
    assert result["task"]["state"] == "needs_revision"
    stored = lessons.get(body["slug"])
    assert stored is not None
    assert stored.status == "needs_revision"
    client = TestClient(app)
    assert client.get(f"/api/lessons/{body['slug']}").status_code == 404


def test_pipeline_publishes_and_is_idempotent(tmp_path: Path):
    lessons = LessonStore(tmp_path / "lessons")
    tasks = TaskStore(tmp_path / "runtime")
    packet = {"topicId": "ef-3-ma-ef03ma01", "lesson": lesson_body()}
    first = run_packet(packet, catalog=app.state.catalog, lessons=lessons, tasks=tasks, provider_configured=False)
    second = run_packet(packet, catalog=app.state.catalog, lessons=lessons, tasks=tasks, provider_configured=False)
    assert first["task"]["state"] == "published"
    assert second["idempotent"] is True
    assert lessons.get("teste-numeros-naturais").status == "published"


def test_generation_endpoint_requires_token():
    client = TestClient(app)
    response = client.post("/api/generation/packets", json={"topicId": "ef-3-ma-ef03ma01"})
    assert response.status_code == 401


def test_provider_gap_does_not_invent_text(tmp_path: Path):
    lessons = LessonStore(tmp_path / "lessons")
    tasks = TaskStore(tmp_path / "runtime")
    result = run_packet(
        {"topicId": "ef-3-ma-ef03ma01", "requiresProvider": True, "lesson": lesson_body()},
        catalog=app.state.catalog,
        lessons=lessons,
        tasks=tasks,
        provider_configured=False,
    )
    assert result["task"]["state"] == "blocked_missing_provider"
    assert lessons.list_lessons() == []
