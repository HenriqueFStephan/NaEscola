#!/usr/bin/env python3
"""Choose five lesson topics with a seeded, stratified random draw.

The history map topic is reserved and Ensino Religioso is excluded. Both
decisions are written into the selection record. Python's random.Random is
seeded with 20261028.
"""

from __future__ import annotations

import json
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261028
RESERVED = "ef-6-hi-ef06hi13"
OUT = ROOT / "content/selection/initial-five.json"


def main() -> None:
    eligible = []
    excluded = [
        {
            "topicId": RESERVED,
            "reason": "Reservado para a aula de História com mapa de territórios. Não entra no sorteio dos cinco.",
        }
    ]
    for grade in (3, 4, 5, 6):
        document = json.loads((ROOT / "curriculum" / f"grade-{grade}.json").read_text(encoding="utf-8"))
        for subject in document["subjects"]:
            for unit in subject["units"]:
                for topic in unit["topics"]:
                    record = {
                        "topicId": topic["id"],
                        "grade": grade,
                        "subjectId": subject["id"],
                        "subject": subject["name"],
                        "sigla": subject["codeSigla"],
                        "name": topic["name"],
                        "code": topic["bnccSkillCodes"][0],
                    }
                    if subject["codeSigla"] == "ER":
                        continue
                    if topic["id"] == RESERVED:
                        continue
                    eligible.append(record)
    excluded.append(
        {
            "component": "Ensino Religioso",
            "reason": "Fora do sorteio inicial. A matrícula é facultativa e a aula não deve inventar conteúdo confessional. As habilidades permanecem no currículo.",
        }
    )
    rng = random.Random(SEED)
    by_grade: dict[int, list[dict]] = {grade: [] for grade in (3, 4, 5, 6)}
    for record in eligible:
        by_grade[record["grade"]].append(record)
    for records in by_grade.values():
        rng.shuffle(records)
    selected = []
    used_subjects = set()
    for grade in (3, 4, 5, 6):
        pick = next((item for item in by_grade[grade] if item["sigla"] not in used_subjects), by_grade[grade][0])
        selected.append(pick)
        used_subjects.add(pick["sigla"])
    remaining = [item for item in eligible if item["topicId"] not in {row["topicId"] for row in selected}]
    preferred = [item for item in remaining if item["sigla"] not in used_subjects]
    pool = preferred or remaining
    rng.shuffle(pool)
    selected.append(pool[0])
    payload = {
        "seed": SEED,
        "generator": f"random.Random({SEED}) from CPython {__import__('sys').version.split()[0]}",
        "selectionDate": "2026-10-28",
        "eligibleCount": len(eligible),
        "exclusions": excluded,
        "selected": selected,
        "reservedHistoryMapTopicId": RESERVED,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
