import json
from pathlib import Path

from app.main import app
from app.schemas.content import Lesson
from app.services.validation import validate_lesson

ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "content" / "lessons"
EXPECTED = {
    "multiplicacao-grupos-e-retangulos",
    "registros-com-nomes",
    "concordancia-e-pontuacao",
    "por-onde-a-musica-circula",
    "lutas-nao-sao-brigas",
    "imperio-no-mundo-antigo",
    "fracoes-unitarias-na-reta",
    "cada-algarismo-no-seu-lugar",
    "por-onde-a-luz-passa",
    "a-agua-muda-e-continua",
    "uma-fase-ou-mais",
    "o-tempo-nao-e-uma-linha-so",
}


def test_every_versioned_lesson_is_publishable():
    found = set()
    for path in LESSONS.glob("*.json"):
        lesson = Lesson.model_validate(json.loads(path.read_text(encoding="utf-8")))
        report = validate_lesson(lesson, app.state.catalog, app.state.lessons)
        assert lesson.status == "published", lesson.slug
        assert report.publishable, [issue.model_dump() for issue in report.issues]
        assert lesson.language == "pt-BR"
        checks = [block for block in lesson.blocks if block.type == "knowledge-check"]
        visuals = [block for block in lesson.blocks if block.type == "visualization"]
        assert len(checks) >= 4, lesson.slug
        assert len(visuals) >= 2, lesson.slug
        for block in checks:
            assert all(choice.explanation.strip() for choice in block.choices), lesson.slug
        found.add(lesson.slug)
    assert found == EXPECTED


def test_history_map_uses_only_documented_states():
    lesson = Lesson.model_validate(json.loads((LESSONS / "imperio-no-mundo-antigo.json").read_text(encoding="utf-8")))
    block = next(item for item in lesson.blocks if item.type == "visualization" and item.component == "territory-map")
    assert block.config["stateIds"] == ["bc323", "bc200", "bc100", "ce100", "ce200", "ce400"]
    assert "aproximad" in block.description
