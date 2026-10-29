from __future__ import annotations

import unicodedata

from app.persistence.catalog import CurriculumCatalog, LessonStore
from app.schemas.content import Lesson

STAGES = [
    {
        "id": "educacao-infantil",
        "label": "Educação Infantil",
        "status": "curriculum_loaded",
        "summary": "Três grupos etários da BNCC, da creche à pré-escola. Os objetivos são oficiais; a ordem é proposta.",
        "gradeIds": ["ei-bebes", "ei-bem-pequenas", "ei-pequenas"],
    },
    {
        "id": "ef-anos-iniciais",
        "label": "Ensino Fundamental I",
        "status": "curriculum_loaded",
        "summary": "1º ao 5º ano, com as habilidades oficiais da BNCC e a sequência proposta pela NaEscola.",
        "gradeIds": ["ef-1", "ef-2", "ef-3", "ef-4", "ef-5"],
    },
    {
        "id": "ef-anos-finais",
        "label": "Ensino Fundamental II",
        "status": "curriculum_loaded",
        "summary": "6º ao 9º ano, com as habilidades oficiais da BNCC e a sequência proposta pela NaEscola.",
        "gradeIds": ["ef-6", "ef-7", "ef-8", "ef-9"],
    },
    {
        "id": "ensino-medio",
        "label": "Ensino Médio",
        "status": "curriculum_loaded",
        "summary": "Habilidades oficiais da etapa, sem série atribuída. As três séries não recebem uma lista nacional inventada.",
        "gradeIds": ["em-etapa", "em-1", "em-2", "em-3"],
    },
    {
        "id": "ensino-superior",
        "label": "Ensino Superior",
        "status": "planned_phase_2",
        "summary": "Fase 2. Não há uma estrutura única de cursos nesta versão.",
        "gradeIds": [],
    },
]

PLANNED_GRADES: dict[str, tuple[str, str, str]] = {}


def coverage_percent(published_count: int, total: int) -> float:
    if not total:
        return 0
    return round(100 * published_count / total, 1)


def aggregate_coverage(grades: list[dict]) -> dict:
    topic_total = sum(int(grade["topicCount"]) for grade in grades)
    published_total = sum(int(grade["publishedLessonCount"]) for grade in grades)
    return {
        "topicCount": topic_total,
        "publishedLessonCount": published_total,
        "coveragePercent": coverage_percent(published_total, topic_total),
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
        "coveragePercent": coverage_percent(published_count, total),
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
        status = "curriculum_loaded"
        if grade.skillPlacement == "series-has-no-official-skills":
            status = "series_without_official_split"
        return {
            "id": grade.gradeId,
            "label": grade.gradeLabel,
            "stageId": grade.stageId,
            "stageLabel": grade.stageLabel,
            "status": status,
            "description": grade.nomenclatureNote,
            "segmentKind": grade.segmentKind,
            "skillPlacement": grade.skillPlacement,
            "officialSkillCatalogId": grade.officialSkillCatalogId,
            "uncertainties": grade.uncertainties,
            "subjects": subjects,
            "publishedLessonCount": published_total,
            "topicCount": topic_total,
            "coveragePercent": coverage_percent(published_total, topic_total),
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
