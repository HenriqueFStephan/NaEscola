from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from app.persistence.catalog import CurriculumCatalog, LessonStore, TaskStore
from app.schemas.content import Lesson, ReviewRecord, TaskRecord
from app.services.validation import validate_lesson


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def packet_key(topic_id: str, packet: dict) -> str:
    digest = hashlib.sha256(json.dumps(packet, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{topic_id}:{digest[:16]}"


def run_packet(
    packet: dict,
    *,
    catalog: CurriculumCatalog,
    lessons: LessonStore,
    tasks: TaskStore,
    provider_configured: bool,
) -> dict:
    """Assemble one lesson from a reviewed research packet.

    This does not call a language model. Without a packet, generation stops.
    A failing gate never writes status "published".
    """
    topic_id = packet.get("topicId")
    if not topic_id or catalog.topic(topic_id) is None:
        raise ValueError("Research packet topic does not exist.")
    key = packet_key(topic_id, packet)
    existing = tasks.find_by_key(key)
    if existing and existing.state == "published" and existing.lessonSlug:
        stored = lessons.get(existing.lessonSlug)
        if stored and stored.status == "published":
            return {"task": existing.model_dump(), "idempotent": True, "report": {"publishable": True, "issues": []}}
    if not tasks.acquire(topic_id):
        return {"blocked": True, "reason": "topic-locked"}
    task = existing or TaskRecord(
        id=f"task-{key}",
        idempotencyKey=key,
        topicId=topic_id,
        state="selected",
        attempts=0,
        message="Pacote de pesquisa recebido.",
        createdAt=now(),
        updatedAt=now(),
    )
    try:
        task.attempts += 1
        task.state = "researching"
        task.updatedAt = now()
        tasks.upsert(task)
        if packet.get("requiresProvider") and not provider_configured:
            task.state = "blocked_missing_provider"
            task.message = "Não há provedor de geração configurado. Nenhum texto foi inventado."
            task.updatedAt = now()
            tasks.upsert(task)
            return {"task": task.model_dump(), "idempotent": False, "report": None}
        task.state = "drafting"
        tasks.upsert(task)
        lesson = Lesson.model_validate(packet["lesson"])
        if lesson.topicId != topic_id:
            raise ValueError("Packet lesson topic does not match the task.")
        if any(item.topicId == topic_id and item.status == "published" for item in lessons.by_topic(topic_id)) and lesson.slug not in {
            item.slug for item in lessons.by_topic(topic_id)
        }:
            task.state = "failed"
            task.message = "Já existe aula publicada para este tópico. A geração não criou outra."
            task.updatedAt = now()
            tasks.upsert(task)
            return {"task": task.model_dump(), "idempotent": False, "report": None}
        task.state = "building_displays"
        tasks.upsert(task)
        task.state = "validation"
        tasks.upsert(task)
        report = validate_lesson(lesson, catalog, lessons)
        task.state = "review"
        task.updatedAt = now()
        tasks.upsert(task)
        if lesson.status == "published" and not report.publishable:
            lesson.status = "needs_revision"
            lessons.save(lesson)
            task.state = "needs_revision"
            task.lessonSlug = lesson.slug
            task.message = "A validação falhou. A aula permaneceu fora de publicação."
            task.updatedAt = now()
            tasks.upsert(task)
            return {"task": task.model_dump(), "idempotent": False, "report": report.model_dump()}
        if lesson.status != "published":
            lessons.save(lesson)
            task.state = "review"
            task.lessonSlug = lesson.slug
            task.message = "Rascunho preservado. Publicação não foi solicitada ou os portões não foram cumpridos."
            task.updatedAt = now()
            tasks.upsert(task)
            return {"task": task.model_dump(), "idempotent": False, "report": report.model_dump()}
        lessons.save(lesson)
        task.state = "published"
        task.lessonSlug = lesson.slug
        task.message = "Publicada depois que os portões de validação passaram."
        task.updatedAt = now()
        tasks.upsert(task)
        return {"task": task.model_dump(), "idempotent": False, "report": report.model_dump()}
    except Exception as exc:  # noqa: BLE001 — task state must record the failure
        task.state = "failed"
        task.message = str(exc)
        task.updatedAt = now()
        tasks.upsert(task)
        return {"task": task.model_dump(), "idempotent": False, "report": None}
    finally:
        tasks.release(topic_id)


def deterministic_review(notes: str) -> ReviewRecord:
    return ReviewRecord(
        id="review-deterministic",
        method="deterministic-schema-source-and-curriculum-gates",
        decision="approve",
        notes=notes,
        createdAt=now(),
    )
