from __future__ import annotations

from app.persistence.catalog import CurriculumCatalog


def edges(catalog: CurriculumCatalog) -> dict[str, list[str]]:
    return {
        topic_id: [link.topicId for link in record["topic"].prerequisites]
        for topic_id, record in catalog.topics.items()
    }


def broken_references(catalog: CurriculumCatalog) -> list[str]:
    known = set(catalog.topics)
    broken = []
    for topic_id, targets in edges(catalog).items():
        for target in targets:
            if target not in known:
                broken.append(f"{topic_id}->{target}")
        for related in catalog.topics[topic_id]["topic"].relatedTopicIds:
            if related not in known:
                broken.append(f"{topic_id}~{related}")
    return broken


def find_cycles(catalog: CurriculumCatalog) -> list[list[str]]:
    graph = edges(catalog)
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[list[str]] = []

    def walk(node: str, stack: list[str]) -> None:
        if node in visiting:
            cycles.append(stack[stack.index(node):] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        for nxt in graph.get(node, []):
            if nxt in graph:
                walk(nxt, stack + [nxt])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        walk(node, [node])
    return cycles


def duplicate_topic_ids(catalog: CurriculumCatalog) -> list[str]:
    # The catalog dict cannot hold duplicates. Scan the raw grade objects.
    seen: set[str] = set()
    duplicates: list[str] = []
    for grade in catalog.grades.values():
        for subject in grade.subjects:
            for unit in subject.units:
                for topic in unit.topics:
                    if topic.id in seen:
                        duplicates.append(topic.id)
                    seen.add(topic.id)
    return duplicates
