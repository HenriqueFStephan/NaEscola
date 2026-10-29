from __future__ import annotations

import argparse
import json
import sys

from app.automation.budget import BudgetManager
from app.automation.window import window_report
from app.generation.pipeline import run_packet
from app.persistence.catalog import CurriculumCatalog, LessonStore, TaskStore
from app.settings import load_settings


def next_topic(catalog: CurriculumCatalog, lessons: LessonStore, *, grade_id: str | None, subject_id: str | None, unit_id: str | None) -> str | None:
    published = {lesson.topicId for lesson in lessons.list_lessons() if lesson.status == "published"}
    for record in catalog.iter_topics():
        topic = record["topic"]
        if topic.id in published:
            continue
        if grade_id and record["grade"].gradeId != grade_id:
            continue
        if subject_id and record["subject"].id != subject_id:
            continue
        if unit_id and record["unit"].id != unit_id:
            continue
        return topic.id
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NaEscola generation commands. Dry-run does not publish.")
    parser.add_argument(
        "command",
        choices=[
            "validate",
            "dry-run",
            "window-check",
            "generate-one",
            "generate-five",
            "next",
            "continue",
            "until-budget",
            "regenerate",
        ],
    )
    parser.add_argument("--packet", help="Research packet JSON. Required to assemble a lesson.")
    parser.add_argument("--grade")
    parser.add_argument("--subject")
    parser.add_argument("--unit")
    parser.add_argument("--topic")
    parser.add_argument("--lesson")
    args = parser.parse_args(argv)
    settings = load_settings()
    catalog = CurriculumCatalog(settings.curriculum_dir)
    lessons = LessonStore(settings.lessons_dir)
    tasks = TaskStore(settings.runtime_dir)

    if args.command == "window-check":
        print(json.dumps(window_report(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "validate":
        from app.services.graph import broken_references, duplicate_topic_ids, find_cycles

        report = {
            "topics": len(catalog.topics),
            "cycles": len(find_cycles(catalog)),
            "brokenReferences": len(broken_references(catalog)),
            "duplicateIds": len(duplicate_topic_ids(catalog)),
            "publishedLessons": sum(1 for lesson in lessons.list_lessons() if lesson.status == "published"),
        }
        print(json.dumps(report, indent=2))
        return 0 if report["cycles"] == 0 and report["brokenReferences"] == 0 and report["duplicateIds"] == 0 else 1
    if args.command == "dry-run":
        topic_id = args.topic or next_topic(catalog, lessons, grade_id=args.grade, subject_id=args.subject, unit_id=args.unit)
        print(json.dumps({
            "mode": "dry-run",
            "wouldSelect": topic_id,
            "providerConfigured": bool(settings.generation_provider),
            "willPublish": False,
            "monthlyAutomationOperational": False,
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command in {"generate-five", "continue", "until-budget", "regenerate", "generate-one", "next"} and not args.packet:
        budget = BudgetManager(settings.runtime_dir / "budget.json", settings.monthly_budget_usd)
        allowed, reason = budget.can_start()
        print(json.dumps({
            "published": False,
            "providerConfigured": bool(settings.generation_provider),
            "budgetAllowsStart": allowed,
            "reason": "Refusing to invent lesson text. Pass --packet to run the deterministic assembler." if not args.packet else reason,
            "nextTopic": next_topic(
                catalog,
                lessons,
                grade_id=args.grade or (f"ef-{args.grade}" if args.grade and args.grade.isdigit() else args.grade),
                subject_id=args.subject,
                unit_id=args.unit,
            ) if args.command in {"next", "generate-one", "continue"} else None,
            "monthlyAutomationOperational": False,
        }, ensure_ascii=False, indent=2))
        return 2
    packet = json.loads(open(args.packet, encoding="utf-8").read())
    result = run_packet(
        packet,
        catalog=catalog,
        lessons=lessons,
        tasks=tasks,
        provider_configured=bool(settings.generation_provider),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    state = (result.get("task") or {}).get("state")
    return 0 if state == "published" or result.get("idempotent") else 1


if __name__ == "__main__":
    sys.exit(main())
