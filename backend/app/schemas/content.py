from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceReference(StrictModel):
    id: str
    title: str
    authorOrInstitution: str
    url: str | None = None
    identifier: str | None = None
    publicationDate: str | None = None
    accessedAt: str
    sourceType: Literal[
        "official-curriculum",
        "government",
        "academic",
        "dataset",
        "reference-work",
        "primary",
    ]
    relevantClaims: list[str] = Field(default_factory=list)
    reliabilityNote: str | None = None
    license: str | None = None

    @model_validator(mode="after")
    def has_locator(self) -> "SourceReference":
        if not self.url and not self.identifier:
            raise ValueError("A reference needs a URL or an identifier.")
        return self


class PrerequisiteLink(StrictModel):
    topicId: str
    kind: Literal["conceptual", "cross-subject", "same-official-code-previous-year"]
    note: str


class SkillRecord(StrictModel):
    code: str
    text: str
    officialYears: list[int]
    placedOnGrade: int
    componentId: str
    documentId: str
    sourceId: str
    sourceLocator: str | None
    pdfLocator: str | None


class Topic(StrictModel):
    id: str
    slug: str
    name: str
    summary: str
    subtopics: list[str]
    bnccSkillCodes: list[str]
    skills: list[SkillRecord]
    learningObjectives: list[str]
    objectiveOrigin: Literal["official-skill-statement"]
    proposedOrder: int
    sequenceKind: Literal["naescola-proposed"]
    sequenceBasis: str
    complexity: Literal["introducao", "desenvolvimento", "consolidacao"]
    lessonTypes: list[str]
    suggestedVisualizations: list[str]
    prerequisites: list[PrerequisiteLink]
    relatedTopicIds: list[str]
    coverageStatus: Literal["planned", "in_progress", "published"]
    flags: list[str]
    camposDeAtuacao: list[str]
    eixo: str | None = None


class Unit(StrictModel):
    id: str
    sourceId: str
    name: str
    kind: Literal["unidade-tematica", "pratica-de-linguagem", "eixo"]
    official: Literal[True]
    sequenceKind: Literal["document-order-adopted-as-naescola-proposal"]
    topics: list[Topic]


class Subject(StrictModel):
    id: str
    slug: str
    name: str
    componentId: str
    codeSigla: str
    areaId: str
    areaName: str
    description: str
    officialStatus: Literal["bncc-2018", "complemento-computacao-2022"]
    localDependencyNote: str | None
    units: list[Unit]


class Omission(StrictModel):
    component: str
    reason: str


class GradeCurriculum(StrictModel):
    schemaVersion: Literal["1.0.0"]
    gradeId: str
    gradeNumber: int
    gradeLabel: str
    stageId: str
    stageLabel: str
    nomenclatureNote: str
    subjects: list[Subject]
    omissions: list[Omission]
    sources: list[SourceReference]
    notes: list[str]


class Choice(StrictModel):
    id: str
    text: str


class ParagraphBlock(StrictModel):
    type: Literal["paragraph"]
    text: str


class HeadingBlock(StrictModel):
    type: Literal["heading"]
    level: Literal[2, 3]
    text: str


class CalloutBlock(StrictModel):
    type: Literal["callout"]
    tone: Literal["objective", "example", "misconception", "uncertainty", "remember"]
    title: str
    text: str


class WorkedExampleBlock(StrictModel):
    type: Literal["worked-example"]
    title: str
    prompt: str
    steps: list[str]
    conclusion: str


class KnowledgeCheckBlock(StrictModel):
    type: Literal["knowledge-check"]
    id: str
    prompt: str
    choices: list[Choice]
    correctChoiceId: str
    feedbackCorrect: str
    feedbackIncorrect: str

    @model_validator(mode="after")
    def one_correct_choice(self) -> "KnowledgeCheckBlock":
        ids = [choice.id for choice in self.choices]
        if len(ids) < 2 or len(ids) != len(set(ids)):
            raise ValueError("A knowledge check needs at least two distinct choices.")
        if self.correctChoiceId not in ids:
            raise ValueError("correctChoiceId must match a choice.")
        return self


class ParameterSpec(StrictModel):
    label: str
    min: float
    max: float
    step: float
    default: float

    @model_validator(mode="after")
    def bounds(self) -> "ParameterSpec":
        if self.step <= 0 or self.min >= self.max:
            raise ValueError("Invalid parameter bounds.")
        if not self.min <= self.default <= self.max:
            raise ValueError("Default is outside the parameter bounds.")
        return self


class FunctionPlotConfig(StrictModel):
    family: Literal["sine", "linear", "quadratic"]
    parameters: dict[str, ParameterSpec]
    xMin: float
    xMax: float
    samples: int = 240
    xLabel: str
    yLabel: str
    yMin: float | None = None
    yMax: float | None = None

    @model_validator(mode="after")
    def allowlist(self) -> "FunctionPlotConfig":
        expected = {
            "sine": {"A", "B", "C", "D"},
            "linear": {"A", "B"},
            "quadratic": {"A", "B", "C"},
        }[self.family]
        if set(self.parameters) != expected:
            raise ValueError(f"{self.family} accepts only {sorted(expected)}.")
        if self.samples < 16 or self.xMin >= self.xMax:
            raise ValueError("Invalid plot domain.")
        return self


class Marker(StrictModel):
    value: float
    label: str


class NumberLineConfig(StrictModel):
    min: float
    max: float
    step: float
    ticks: list[float]
    markers: list[Marker]
    initial: float

    @model_validator(mode="after")
    def bounds(self) -> "NumberLineConfig":
        if self.step <= 0 or self.min >= self.max or not self.min <= self.initial <= self.max:
            raise ValueError("Invalid number line.")
        return self


class Point(StrictModel):
    x: float
    y: float


class GeometryPolygon(StrictModel):
    points: list[Point]
    label: str
    fill: str


class GeometryConfig(StrictModel):
    width: int
    height: int
    polygons: list[GeometryPolygon]
    caption: str
    toggleLabel: str | None = None
    alternatePolygons: list[GeometryPolygon] | None = None


class ComparisonRow(StrictModel):
    label: str
    left: str
    right: str


class ComparisonConfig(StrictModel):
    leftTitle: str
    rightTitle: str
    rows: list[ComparisonRow]


class TimelineEvent(StrictModel):
    id: str
    label: str
    text: str


class EventTimelineConfig(StrictModel):
    events: list[TimelineEvent]


class BarItem(StrictModel):
    id: str
    label: str
    value: float


class BarCompareConfig(StrictModel):
    unit: str
    bars: list[BarItem]
    question: str


class StepItem(StrictModel):
    id: str
    title: str
    text: str


class StateStepsConfig(StrictModel):
    steps: list[StepItem]


class MapNarrative(StrictModel):
    stateId: str
    title: str
    text: str


class TerritoryMapConfig(StrictModel):
    datasetId: Literal["mediterranean-reconstructions-v1"]
    stateIds: list[str]
    focusNames: list[str]
    narratives: list[MapNarrative]


class ArrayGridConfig(StrictModel):
    allowedRows: list[int]
    allowedColumns: list[int]
    initialRows: int
    initialColumns: int

    @model_validator(mode="after")
    def factors(self) -> "ArrayGridConfig":
        if self.initialRows not in self.allowedRows or self.initialColumns not in self.allowedColumns:
            raise ValueError("Initial array size must be one of the allowed factors.")
        if any(value < 1 for value in [*self.allowedRows, *self.allowedColumns]):
            raise ValueError("Array factors must be positive.")
        return self


class RecordField(StrictModel):
    id: str
    label: str
    value: str


class FieldRecordConfig(StrictModel):
    prompt: str
    targetFieldId: str
    fields: list[RecordField]
    feedbackCorrect: str
    feedbackIncorrect: str

    @model_validator(mode="after")
    def target_exists(self) -> "FieldRecordConfig":
        if self.targetFieldId not in {field.id for field in self.fields}:
            raise ValueError("targetFieldId must match a field.")
        return self


class VisualizationBlock(StrictModel):
    type: Literal["visualization"]
    component: Literal[
        "function-plot",
        "number-line",
        "geometry-diagram",
        "comparison",
        "event-timeline",
        "bar-compare",
        "state-steps",
        "territory-map",
        "array-grid",
        "field-record",
    ]
    title: str
    description: str
    config: dict

    @model_validator(mode="after")
    def typed_config(self) -> "VisualizationBlock":
        models = {
            "function-plot": FunctionPlotConfig,
            "number-line": NumberLineConfig,
            "geometry-diagram": GeometryConfig,
            "comparison": ComparisonConfig,
            "event-timeline": EventTimelineConfig,
            "bar-compare": BarCompareConfig,
            "state-steps": StateStepsConfig,
            "territory-map": TerritoryMapConfig,
            "array-grid": ArrayGridConfig,
            "field-record": FieldRecordConfig,
        }
        models[self.component].model_validate(self.config)
        return self


class SummaryBlock(StrictModel):
    type: Literal["summary"]
    points: list[str]


LessonBlock = Annotated[
    Union[
        ParagraphBlock,
        HeadingBlock,
        CalloutBlock,
        WorkedExampleBlock,
        KnowledgeCheckBlock,
        VisualizationBlock,
        SummaryBlock,
    ],
    Field(discriminator="type"),
]


class ReviewRecord(StrictModel):
    id: str
    method: str
    decision: Literal["approve", "reject"]
    notes: str
    createdAt: str


class Lesson(StrictModel):
    id: str
    slug: str
    title: str
    language: Literal["pt-BR"]
    gradeId: str
    subjectId: str
    unitId: str
    topicId: str
    learningObjectives: list[str]
    bnccSkillCodes: list[str]
    prerequisiteLessonIds: list[str] = Field(default_factory=list)
    blocks: list[LessonBlock]
    references: list[SourceReference]
    status: Literal["planned", "draft", "review", "published", "needs_revision"]
    version: int
    createdAt: str
    updatedAt: str
    sequenceNote: str
    uncertaintyNotes: list[str] = Field(default_factory=list)
    reviews: list[ReviewRecord] = Field(default_factory=list)


class ValidationIssue(StrictModel):
    code: str
    message: str
    severity: Literal["error", "warning"]


class ValidationReport(StrictModel):
    lessonId: str | None
    publishable: bool
    issues: list[ValidationIssue]


class TaskRecord(StrictModel):
    id: str
    idempotencyKey: str
    topicId: str
    state: Literal[
        "planned",
        "selected",
        "researching",
        "drafting",
        "building_displays",
        "validation",
        "review",
        "published",
        "failed",
        "needs_revision",
        "blocked_missing_provider",
    ]
    attempts: int
    message: str
    lessonSlug: str | None = None
    createdAt: str
    updatedAt: str
