from __future__ import annotations

import json

from fastapi import APIRouter, Header, HTTPException, Request

from app.services.reading import (
    STAGES,
    aggregate_coverage,
    grade_summary,
    published_by_topic,
    search,
    subject_stats,
    topic_payload,
)

router = APIRouter(prefix="/api")


def _published(request: Request):
    return published_by_topic(request.app.state.lessons.list_lessons())


@router.get("/health")
def health(request: Request) -> dict:
    catalog = request.app.state.catalog
    return {
        "status": "ok",
        "grades": sorted(catalog.grades),
        "topics": len(catalog.topics),
        "publishedLessons": sum(1 for lesson in request.app.state.lessons.list_lessons() if lesson.status == "published"),
        "generationProviderConfigured": bool(request.app.state.settings.generation_provider),
        "monthlyAutomationOperational": False,
    }


@router.get("/stages")
def stages(request: Request) -> dict:
    catalog = request.app.state.catalog
    lessons = request.app.state.lessons
    payload = []
    for stage in STAGES:
        grade_cards = []
        for grade_id in stage["gradeIds"]:
            summary = grade_summary(catalog, lessons, grade_id)
            if summary:
                grade_cards.append(
                    {
                        "id": summary["id"],
                        "label": summary["label"],
                        "status": summary["status"],
                        "topicCount": summary["topicCount"],
                        "publishedLessonCount": summary["publishedLessonCount"],
                        "coveragePercent": summary["coveragePercent"],
                    }
                )
        payload.append({**stage, **aggregate_coverage(grade_cards), "grades": grade_cards})
    return {"stages": payload}


@router.get("/stages/{stage_id}")
def stage_detail(stage_id: str, request: Request) -> dict:
    catalog = request.app.state.catalog
    lessons = request.app.state.lessons
    for stage in STAGES:
        if stage["id"] != stage_id:
            continue
        grades = [grade_summary(catalog, lessons, grade_id) for grade_id in stage["gradeIds"]]
        grades = [grade for grade in grades if grade is not None]
        return {**stage, **aggregate_coverage(grades), "grades": grades}
    raise HTTPException(status_code=404, detail="Etapa não encontrada.")


@router.get("/grades/{grade_id}")
def grade_detail(grade_id: str, request: Request) -> dict:
    summary = grade_summary(request.app.state.catalog, request.app.state.lessons, grade_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Ano não encontrado.")
    return summary


@router.get("/grades/{grade_id}/subjects/{subject_id}")
def subject_detail(grade_id: str, subject_id: str, request: Request) -> dict:
    catalog = request.app.state.catalog
    grade = catalog.grades.get(grade_id)
    if grade is None:
        raise HTTPException(status_code=404, detail="Ano sem currículo carregado.")
    subject = next((item for item in grade.subjects if item.id == subject_id), None)
    if subject is None:
        raise HTTPException(status_code=404, detail="Componente não encontrado.")
    published = _published(request)
    units = []
    for unit in subject.units:
        topics = []
        for topic in unit.topics:
            record = catalog.topic(topic.id)
            topics.append(topic_payload(record, published))
        units.append(
            {
                "id": unit.id,
                "name": unit.name,
                "kind": unit.kind,
                "sequenceKind": unit.sequenceKind,
                "topics": topics,
            }
        )
    return {
        "gradeId": grade.gradeId,
        "gradeLabel": grade.gradeLabel,
        "subject": {
            **subject.model_dump(exclude={"units"}),
            **subject_stats(subject, published),
            "units": units,
        },
        "sequenceNote": "A linha do tempo mostra a sequência proposta pela NaEscola. Os códigos BNCC continuam oficiais e não viram, sozinhos, uma ordem obrigatória de aulas.",
    }


@router.get("/topics/{topic_id}")
def topic_detail(topic_id: str, request: Request) -> dict:
    record = request.app.state.catalog.topic(topic_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Tópico não encontrado.")
    return {
        "gradeId": record["grade"].gradeId,
        "gradeLabel": record["grade"].gradeLabel,
        "subjectId": record["subject"].id,
        "subjectName": record["subject"].name,
        "unitId": record["unit"].id,
        "unitName": record["unit"].name,
        "topic": topic_payload(record, _published(request)),
    }


@router.get("/search")
def search_content(q: str, request: Request) -> dict:
    return search(request.app.state.catalog, request.app.state.lessons, q)


@router.get("/lessons/{slug}")
def lesson_detail(slug: str, request: Request) -> dict:
    lesson = request.app.state.lessons.get(slug)
    if lesson is None or lesson.status != "published":
        raise HTTPException(status_code=404, detail="Aula publicada não encontrada.")
    record = request.app.state.catalog.topic(lesson.topicId)
    neighbors = _neighbors(request, lesson.topicId)
    published = _published(request)
    prerequisites = []
    for link in record["topic"].prerequisites:
        target = request.app.state.catalog.topic(link.topicId)
        if target is None:
            continue
        lessons_for_topic = published.get(link.topicId, [])
        prerequisites.append(
            {
                "topicId": link.topicId,
                "kind": link.kind,
                "note": link.note,
                "name": target["topic"].name,
                "gradeLabel": target["grade"].gradeLabel,
                "subjectName": target["subject"].name,
                "lessonSlug": lessons_for_topic[0].slug if lessons_for_topic else None,
            }
        )
    return {
        "lesson": lesson.model_dump(),
        "placement": {
            "gradeLabel": record["grade"].gradeLabel,
            "subjectName": record["subject"].name,
            "unitName": record["unit"].name,
            "topicName": record["topic"].name,
            "proposedOrder": record["topic"].proposedOrder,
            "officialSkillText": record["topic"].summary,
        },
        "prerequisites": prerequisites,
        "neighbors": neighbors,
    }


def _neighbors(request: Request, topic_id: str) -> dict:
    record = request.app.state.catalog.topic(topic_id)
    topics = [topic for unit in record["subject"].units for topic in unit.topics]
    index = next(i for i, topic in enumerate(topics) if topic.id == topic_id)
    published = _published(request)

    def link(topic):
        if topic is None:
            return None
        lessons = published.get(topic.id, [])
        return {
            "topicId": topic.id,
            "name": topic.name,
            "lessonSlug": lessons[0].slug if lessons else None,
        }

    return {
        "previous": link(topics[index - 1] if index > 0 else None),
        "next": link(topics[index + 1] if index + 1 < len(topics) else None),
    }


@router.get("/competencies")
def competencies(request: Request) -> dict:
    return request.app.state.catalog.competencies


@router.get("/maps/mediterranean/manifest")
def map_manifest(request: Request) -> dict:
    path = request.app.state.settings.maps_dir / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/maps/mediterranean/glosses")
def map_glosses(request: Request) -> dict:
    path = request.app.state.settings.maps_dir / "glosses.json"
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/maps/mediterranean/{state_id}")
def map_state(state_id: str, request: Request) -> dict:
    allowed = {"bc323", "bc200", "bc100", "ce100", "ce200", "ce400"}
    if state_id not in allowed:
        raise HTTPException(status_code=404, detail="Recorte de mapa não documentado.")
    path = request.app.state.settings.maps_dir / f"{state_id}.geojson"
    return json.loads(path.read_text(encoding="utf-8"))


def require_admin(request: Request, token: str | None) -> None:
    expected = request.app.state.settings.admin_token
    if not expected or token != expected:
        raise HTTPException(status_code=401, detail="Publicação e geração exigem NAESCOLA_ADMIN_TOKEN.")


@router.post("/generation/packets")
def run_generation(payload: dict, request: Request, x_naescola_admin_token: str | None = Header(default=None)) -> dict:
    require_admin(request, x_naescola_admin_token)
    from app.generation.pipeline import run_packet

    try:
        return run_packet(
            payload,
            catalog=request.app.state.catalog,
            lessons=request.app.state.lessons,
            tasks=request.app.state.tasks,
            provider_configured=bool(request.app.state.settings.generation_provider),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/generation/tasks/{task_id}")
def generation_task(task_id: str, request: Request, x_naescola_admin_token: str | None = Header(default=None)) -> dict:
    require_admin(request, x_naescola_admin_token)
    task = next((item for item in request.app.state.tasks.list_tasks() if item.id == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    return task.model_dump()
