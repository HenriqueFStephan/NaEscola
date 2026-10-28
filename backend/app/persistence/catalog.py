from __future__ import annotations

import json
from pathlib import Path

from app.schemas.content import GradeCurriculum, Lesson, TaskRecord


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class CurriculumCatalog:
    def __init__(self, curriculum_dir: Path) -> None:
        self.grades: dict[str, GradeCurriculum] = {}
        self.topics: dict[str, dict] = {}
        self.competencies = read_json(curriculum_dir / "competencies.json")
        self.report = read_json(curriculum_dir / "report.json")
        for path in sorted(curriculum_dir.glob("grade-*.json")):
            grade = GradeCurriculum.model_validate(read_json(path))
            self.grades[grade.gradeId] = grade
            for subject in grade.subjects:
                for unit in subject.units:
                    for topic in unit.topics:
                        self.topics[topic.id] = {
                            "grade": grade,
                            "subject": subject,
                            "unit": unit,
                            "topic": topic,
                        }
        if set(self.grades) != {"ef-3", "ef-4", "ef-5", "ef-6"}:
            raise RuntimeError("Curriculum catalog is missing a required grade.")

    def topic(self, topic_id: str) -> dict | None:
        return self.topics.get(topic_id)

    def iter_topics(self):
        return self.topics.values()


class LessonStore:
    def __init__(self, lessons_dir: Path) -> None:
        self.lessons_dir = lessons_dir
        self.lessons_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, slug: str) -> Path:
        return self.lessons_dir / f"{slug}.json"

    def list_lessons(self) -> list[Lesson]:
        lessons = []
        for path in sorted(self.lessons_dir.glob("*.json")):
            lessons.append(Lesson.model_validate(read_json(path)))
        return lessons

    def get(self, slug: str) -> Lesson | None:
        path = self.path_for(slug)
        if not path.exists():
            return None
        return Lesson.model_validate(read_json(path))

    def save(self, lesson: Lesson) -> None:
        write_json(self.path_for(lesson.slug), lesson.model_dump())

    def by_topic(self, topic_id: str) -> list[Lesson]:
        return [lesson for lesson in self.list_lessons() if lesson.topicId == topic_id]


class TaskStore:
    def __init__(self, runtime_dir: Path) -> None:
        self.path = runtime_dir / "generation-tasks.json"
        self.locks = runtime_dir / "locks"
        self.locks.mkdir(parents=True, exist_ok=True)
        self.runtime_dir = runtime_dir

    def list_tasks(self) -> list[TaskRecord]:
        if not self.path.exists():
            return []
        return [TaskRecord.model_validate(item) for item in read_json(self.path)]

    def save_all(self, tasks: list[TaskRecord]) -> None:
        write_json(self.path, [task.model_dump() for task in tasks])

    def upsert(self, task: TaskRecord) -> None:
        tasks = [item for item in self.list_tasks() if item.id != task.id]
        tasks.append(task)
        self.save_all(tasks)

    def find_by_key(self, key: str) -> TaskRecord | None:
        return next((task for task in self.list_tasks() if task.idempotencyKey == key), None)

    def acquire(self, topic_id: str) -> bool:
        lock = self.locks / f"{topic_id}.lock"
        if lock.exists():
            return False
        lock.write_text(topic_id, encoding="utf-8")
        return True

    def release(self, topic_id: str) -> None:
        lock = self.locks / f"{topic_id}.lock"
        if lock.exists():
            lock.unlink()
