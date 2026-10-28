from __future__ import annotations

from app.persistence.catalog import CurriculumCatalog, LessonStore
from app.schemas.content import Lesson, ValidationIssue, ValidationReport

MAP_STATES = ["bc323", "bc200", "bc100", "ce100", "ce200", "ce400"]


def validate_lesson(
    lesson: Lesson,
    catalog: CurriculumCatalog,
    lessons: LessonStore,
) -> ValidationReport:
    issues: list[ValidationIssue] = []

    def error(code: str, message: str) -> None:
        issues.append(ValidationIssue(code=code, message=message, severity="error"))

    record = catalog.topic(lesson.topicId)
    if record is None:
        error("topic", "O tópico da aula não existe no currículo.")
    else:
        if lesson.gradeId != record["grade"].gradeId:
            error("grade", "O ano da aula não corresponde ao tópico.")
        if lesson.subjectId != record["subject"].id:
            error("subject", "O componente da aula não corresponde ao tópico.")
        if lesson.unitId != record["unit"].id:
            error("unit", "A unidade da aula não corresponde ao tópico.")
        official = set(record["topic"].bnccSkillCodes)
        if not lesson.bnccSkillCodes or any(code not in official for code in lesson.bnccSkillCodes):
            error("bncc", "A aula cita um código que não pertence a este tópico.")
    if not lesson.learningObjectives:
        error("objectives", "A aula precisa de objetivos de aprendizagem.")
    if not any(block.type == "paragraph" for block in lesson.blocks):
        error("paragraph", "A aula precisa de texto explicativo.")
    if not any(block.type == "summary" for block in lesson.blocks):
        error("summary", "A aula precisa de um resumo.")
    if not any(block.type == "knowledge-check" for block in lesson.blocks):
        error("practice", "A aula precisa de uma verificação com retorno explicativo.")
    if not any(block.type == "visualization" for block in lesson.blocks):
        error("visualization", "A aula precisa de uma representação que não seja só texto.")
    if not lesson.references:
        error("references", "A aula precisa de referências.")
    for reference in lesson.references:
        if not reference.title or not reference.authorOrInstitution:
            error("reference-shape", f"Referência {reference.id} está incompleta.")
    for slug in lesson.prerequisiteLessonIds:
        if slug != lesson.slug and lessons.get(slug) is None:
            error("prerequisite-lesson", f"A aula pré-requisito {slug} não existe.")
    for block in lesson.blocks:
        if block.type != "visualization" or block.component != "territory-map":
            continue
        state_ids = block.config["stateIds"]
        ordered = [item for item in MAP_STATES if item in state_ids]
        if not state_ids or state_ids != ordered or any(item not in MAP_STATES for item in state_ids):
            error("map-states", "O mapa só pode usar recortes documentados, sem anos intermediários.")
    approvals = [review for review in lesson.reviews if review.decision == "approve" and review.method.strip()]
    if not approvals:
        error("review", "Publicar exige revisão com método explícito. A ausência de revisão não é aprovada em silêncio.")
    if any(review.decision == "reject" for review in lesson.reviews):
        error("rejected", "Uma revisão de rejeição impede a publicação.")
    publishable = not issues
    return ValidationReport(lessonId=lesson.id, publishable=publishable, issues=issues)
