from __future__ import annotations

import unicodedata

from app.persistence.catalog import CurriculumCatalog, LessonStore
from app.schemas.content import Lesson

STAGES = [
    {
        "id": "educacao-infantil",
        "label": "Educação Infantil",
        "status": "not_researched",
        "summary": "Creche e pré-escola. Ainda não há currículo carregado nesta versão.",
        "gradeIds": [],
    },
    {
        "id": "ef-anos-iniciais",
        "label": "Ensino Fundamental — Anos Iniciais",
        "status": "partial",
        "summary": "1º ao 5º ano. Nesta versão, o currículo carregado é o dos 3º, 4º e 5º anos.",
        "gradeIds": ["ef-1", "ef-2", "ef-3", "ef-4", "ef-5"],
    },
    {
        "id": "ef-anos-finais",
        "label": "Ensino Fundamental — Anos Finais",
        "status": "partial",
        "summary": "6º ao 9º ano. Nesta versão, o currículo carregado é o do 6º ano.",
        "gradeIds": ["ef-6", "ef-7", "ef-8", "ef-9"],
    },
    {
        "id": "ensino-medio",
        "label": "Ensino Médio",
        "status": "not_researched",
        "summary": "1ª, 2ª e 3ª séries. Ainda não há currículo carregado nesta versão.",
        "gradeIds": [],
    },
    {
        "id": "ensino-superior",
        "label": "Ensino Superior",
        "status": "planned_phase_2",
        "summary": "Fase 2. Não há uma estrutura única de cursos nesta versão.",
        "gradeIds": [],
    },
]

PLANNED_GRADES = {
    "ef-1": ("1º ano", "ef-anos-iniciais", "Ensino Fundamental — Anos Iniciais"),
    "ef-2": ("2º ano", "ef-anos-iniciais", "Ensino Fundamental — Anos Iniciais"),
    "ef-7": ("7º ano", "ef-anos-finais", "Ensino Fundamental — Anos Finais"),
    "ef-8": ("8º ano", "ef-anos-finais", "Ensino Fundamental — Anos Finais"),
    "ef-9": ("9º ano", "ef-anos-finais", "Ensino Fundamental — Anos Finais"),
}


def fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def published_by_topic(lessons: list[Lesson]) -> dict[str, list[Lesson]]:
    grouped: dict[str, list[Lesson]] = {}
    for lesson in lessons:
        if lesson.status == "published":
            grouped.setdefault(lesson.topicId, []).append(lesson)
    return grouped


def topic_payload(record: dict, published: dict[str, list[Lesson]]) -> dict:
    topic = record["topic"].model_dump()
    lessons = published.get(topic["id"], [])
    topic["coverageStatus"] = "published" if lessons else topic["coverageStatus"]
    topic["publishedLessonCount"] = len(lessons)
    topic["publishedLessonSlugs"] = [lesson.slug for lesson in lessons]
    return topic


def subject_stats(subject, published: dict[str, list[Lesson]]) -> dict:
    topics = [topic for unit in subject.units for topic in unit.topics]
    published_count = sum(1 for topic in topics if topic.id in published)
    total = len(topics)
    return {
        "topicCount": total,
        "publishedLessonCount": published_count,
        "coveragePercent": round(100 * published_count / total, 1) if total else 0,
    }


def grade_summary(catalog: CurriculumCatalog, lessons: LessonStore, grade_id: str) -> dict | None:
    published = published_by_topic(lessons.list_lessons())
    if grade_id in catalog.grades:
        grade = catalog.grades[grade_id]
        subjects = []
        published_total = 0
        topic_total = 0
        for subject in grade.subjects:
            stats = subject_stats(subject, published)
            published_total += stats["publishedLessonCount"]
            topic_total += stats["topicCount"]
            subjects.append(
                {
                    "id": subject.id,
                    "name": subject.name,
                    "slug": subject.slug,
                    "officialStatus": subject.officialStatus,
                    "description": subject.description,
                    **stats,
                }
            )
        return {
            "id": grade.gradeId,
            "label": grade.gradeLabel,
            "stageId": grade.stageId,
            "stageLabel": grade.stageLabel,
            "status": "curriculum_loaded",
            "description": grade.nomenclatureNote,
            "subjects": subjects,
            "publishedLessonCount": published_total,
            "topicCount": topic_total,
            "coveragePercent": round(100 * published_total / topic_total, 1) if topic_total else 0,
            "omissions": [item.model_dump() for item in grade.omissions],
        }
    planned = PLANNED_GRADES.get(grade_id)
    if not planned:
        return None
    label, stage_id, stage_label = planned
    return {
        "id": grade_id,
        "label": label,
        "stageId": stage_id,
        "stageLabel": stage_label,
        "status": "not_researched",
        "description": "Ano previsto na estrutura da educação básica. O currículo ainda não foi carregado.",
        "subjects": [],
        "publishedLessonCount": 0,
        "topicCount": 0,
        "coveragePercent": 0,
        "omissions": [],
    }


def search(catalog: CurriculumCatalog, lessons: LessonStore, query: str) -> dict:
    needle = fold(query.strip())
    topics = []
    lesson_hits = []
    if len(needle) < 2:
        return {"query": query, "topics": [], "lessons": []}
    for record in catalog.iter_topics():
        topic = record["topic"]
        haystack = " ".join(
            [
                topic.name,
                topic.summary,
                " ".join(topic.bnccSkillCodes),
                record["subject"].name,
                record["grade"].gradeLabel,
            ]
        )
        if needle in fold(haystack):
            topics.append(
                {
                    "topicId": topic.id,
                    "name": topic.name,
                    "gradeId": record["grade"].gradeId,
                    "gradeLabel": record["grade"].gradeLabel,
                    "subjectId": record["subject"].id,
                    "subjectName": record["subject"].name,
                    "bnccSkillCodes": topic.bnccSkillCodes,
                }
            )
            if len(topics) >= 40:
                break
    for lesson in lessons.list_lessons():
        if lesson.status != "published":
            continue
        haystack = f"{lesson.title} {' '.join(lesson.bnccSkillCodes)}"
        if needle in fold(haystack):
            lesson_hits.append({"slug": lesson.slug, "title": lesson.title, "gradeId": lesson.gradeId})
    return {"query": query, "topics": topics, "lessons": lesson_hits}
