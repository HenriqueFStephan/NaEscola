#!/usr/bin/env python3
"""Build NaEscola curriculum files for grades 3–6 from pinned BNCC sources.

Official skill statements are copied from the pinned dataset. Teaching order,
complexity, and prerequisite links are NaEscola proposals and are labeled as
such. The script fails if an expected skill code is missing or its text does
not contain the checked phrase.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BNCC_PATH = ROOT / "data/sources/bncc-2018/ensino-fundamental.json"
STRUCTURE_PATH = ROOT / "data/sources/bncc-2018/estrutura.json"
COMPUTING_PATH = ROOT / "data/sources/computacao-2022/computacao.json"
OUT_DIR = ROOT / "curriculum"
DOCS_DIR = ROOT / "docs/curriculum"

DATASET_COMMIT = "9c268978efa2aa250834c6a9edb6074432752838"
DATASET_VERSION = "dados-2026.07.1"
DATASET_CITATION = "Profy. bncc.dev: dados abertos e verificados da Base Nacional Comum Curricular. versão dados-2026.07.1. DOI 10.5281/zenodo.21881682."
MAP_COMMIT = "da7a4b735ecef70aebdc9c73e409d8a2500d50f3"
GRADES = (3, 4, 5, 6)
SUBJECT_ORDER = ("LP", "MA", "CI", "HI", "GE", "AR", "EF", "LI", "ER", "CO")
SEQUENCE_BASIS = (
    "Ordem de apresentação no documento oficial, adotada como sequência proposta "
    "pela NaEscola. A BNCC não define esta ordem como sequência obrigatória de aulas."
)
LINE_RE = re.compile(r"linha\s+(\d+)", re.IGNORECASE)

DESCRIPTIONS = {
    "LP": "Leitura, escrita, oralidade e análise de textos em língua portuguesa, com as habilidades oficiais da BNCC para este ano.",
    "MA": "Números, álgebra, geometria, grandezas e probabilidade, na progressão proposta pela NaEscola a partir das habilidades oficiais.",
    "CI": "Matéria, vida, Terra e tecnologia, conforme as unidades temáticas e habilidades da BNCC para este ano.",
    "HI": "Processos históricos previstos na BNCC para este ano. A cronologia dos acontecimentos não é, por si só, a ordem obrigatória das aulas.",
    "GE": "Lugar, paisagem, território e representação do espaço, com as habilidades oficiais de Geografia.",
    "AR": "Artes visuais, dança, música, teatro e artes integradas, no bloco de anos definido pela BNCC.",
    "EF": "Brincadeiras, esportes, danças, ginásticas, lutas e práticas de aventura, como componente curricular, não como recreio.",
    "LI": "Língua inglesa a partir do 6º ano, com eixos de oralidade, leitura, escrita e conhecimentos linguísticos.",
    "ER": "Componente da BNCC de matrícula facultativa nas escolas públicas. A NaEscola registra as habilidades oficiais e não produz doutrina confessional.",
    "CO": "Complemento de Computação do Parecer CNE/CEB nº 2/2022. Não faz parte do texto homologado da BNCC de 2018.",
}

LESSON_TYPES = {
    "LP": ["explicacao", "exemplos", "pratica"],
    "MA": ["explicacao", "exemplos", "pratica"],
    "CI": ["explicacao", "observacao", "pratica"],
    "HI": ["explicacao", "linha-do-tempo", "fontes"],
    "GE": ["explicacao", "representacao-espacial", "pratica"],
    "AR": ["explicacao", "apreciacao", "pratica"],
    "EF": ["explicacao", "pratica-corporal"],
    "LI": ["explicacao", "exemplos", "pratica"],
    "ER": ["explicacao", "comparacao"],
    "CO": ["explicacao", "exemplo-passo-a-passo", "pratica"],
}

VISUALS = {
    "LP": ["comparison"],
    "MA": ["number-line", "comparison"],
    "CI": ["state-steps", "comparison"],
    "HI": ["event-timeline"],
    "GE": ["comparison"],
    "AR": ["comparison"],
    "EF": ["state-steps"],
    "LI": ["comparison"],
    "ER": ["comparison"],
    "CO": ["state-steps", "comparison"],
}

# Dependent code -> prerequisite codes. All are NaEscola conceptual proposals.
CONCEPTUAL_EDGES: list[tuple[str, str, str]] = [
    ("EF03MA02", "EF03MA01", "conceptual"),
    ("EF03MA03", "EF03MA01", "conceptual"),
    ("EF03MA05", "EF03MA03", "conceptual"),
    ("EF03MA06", "EF03MA05", "conceptual"),
    ("EF03MA07", "EF03MA03", "conceptual"),
    ("EF03MA08", "EF03MA07", "conceptual"),
    ("EF03MA09", "EF03MA08", "conceptual"),
    ("EF03MA11", "EF03MA06", "conceptual"),
    ("EF03MA14", "EF03MA13", "conceptual"),
    ("EF04MA01", "EF03MA01", "conceptual"),
    ("EF04MA02", "EF04MA01", "conceptual"),
    ("EF04MA03", "EF03MA06", "conceptual"),
    ("EF04MA06", "EF03MA07", "conceptual"),
    ("EF04MA07", "EF04MA06", "conceptual"),
    ("EF04MA09", "EF03MA09", "conceptual"),
    ("EF04MA10", "EF04MA09", "conceptual"),
    ("EF04MA14", "EF03MA11", "conceptual"),
    ("EF04MA15", "EF04MA14", "conceptual"),
    ("EF04MA17", "EF03MA14", "conceptual"),
    ("EF05MA01", "EF04MA01", "conceptual"),
    ("EF05MA02", "EF04MA10", "conceptual"),
    ("EF05MA03", "EF04MA09", "conceptual"),
    ("EF05MA04", "EF05MA03", "conceptual"),
    ("EF05MA05", "EF05MA04", "conceptual"),
    ("EF05MA05", "EF05MA02", "conceptual"),
    ("EF05MA06", "EF05MA04", "conceptual"),
    ("EF05MA07", "EF04MA03", "conceptual"),
    ("EF05MA07", "EF05MA02", "conceptual"),
    ("EF05MA08", "EF05MA07", "conceptual"),
    ("EF05MA08", "EF04MA06", "conceptual"),
    ("EF05MA10", "EF04MA14", "conceptual"),
    ("EF05MA11", "EF05MA10", "conceptual"),
    ("EF05MA11", "EF04MA15", "conceptual"),
    ("EF05MA15", "EF05MA14", "conceptual"),
    ("EF05MA16", "EF04MA17", "conceptual"),
    ("EF05MA17", "EF03MA15", "conceptual"),
    ("EF06MA01", "EF05MA01", "conceptual"),
    ("EF06MA01", "EF05MA02", "conceptual"),
    ("EF06MA03", "EF05MA08", "conceptual"),
    ("EF06MA07", "EF05MA04", "conceptual"),
    ("EF06MA07", "EF05MA05", "conceptual"),
    ("EF06MA08", "EF06MA07", "conceptual"),
    ("EF06MA08", "EF05MA02", "conceptual"),
    ("EF06MA09", "EF06MA07", "conceptual"),
    ("EF06MA10", "EF06MA07", "conceptual"),
    ("EF06MA11", "EF06MA08", "conceptual"),
    ("EF06MA11", "EF06MA03", "conceptual"),
    ("EF06MA13", "EF05MA06", "conceptual"),
    ("EF06MA14", "EF05MA10", "conceptual"),
    ("EF06MA16", "EF05MA15", "conceptual"),
    ("EF06MA18", "EF05MA17", "conceptual"),
    ("EF06MA19", "EF06MA18", "conceptual"),
    ("EF06MA20", "EF06MA18", "conceptual"),
    ("EF06HI10", "EF06HI09", "conceptual"),
    ("EF06HI11", "EF06HI10", "conceptual"),
    ("EF06HI12", "EF06HI11", "conceptual"),
    ("EF06HI13", "EF06HI11", "conceptual"),
    ("EF06HI08", "EF06HI07", "conceptual"),
    ("EF04GE10", "EF03GE06", "cross-subject"),
    ("EF06GE08", "EF04GE10", "cross-subject"),
    ("EF06HI06", "EF04GE10", "cross-subject"),
]

TEXT_CHECKS = {
    "EF03MA01": "números naturais",
    "EF03MA02": "sistema de numeração decimal",
    "EF03MA03": "adição",
    "EF03MA05": "adição e subtração",
    "EF03MA06": "adição e subtração",
    "EF03MA07": "multiplicação",
    "EF03MA08": "divisão",
    "EF03MA09": "metade",
    "EF03MA11": "igualdade",
    "EF03MA13": "figuras geométricas espaciais",
    "EF03MA14": "planificações",
    "EF03MA15": "figuras planas",
    "EF03GE06": "representação cartográfica",
    "EF04MA01": "números naturais",
    "EF04MA02": "potências de dez",
    "EF04MA03": "adição e subtração",
    "EF04MA06": "multiplicação",
    "EF04MA07": "divisão",
    "EF04MA09": "frações unitárias",
    "EF04MA10": "decimal",
    "EF04MA14": "igualdade",
    "EF04MA15": "número desconhecido",
    "EF04MA17": "prismas",
    "EF04GE10": "mapas",
    "EF05MA01": "números naturais",
    "EF05MA02": "decimais" if False else "decimal",
    "EF05MA03": "frações",
    "EF05MA04": "frações equivalentes",
    "EF05MA05": "reta numérica",
    "EF05MA06": "10%",
    "EF05MA07": "adição e subtração",
    "EF05MA08": "multiplicação e divisão",
    "EF05MA10": "igualdade",
    "EF05MA11": "desconhecido",
    "EF05MA14": "localização",
    "EF05MA15": "plano cartesiano",
    "EF05MA16": "planificações",
    "EF05MA17": "polígonos",
    "EF06MA01": "números naturais",
    "EF06MA03": "números naturais",
    "EF06MA07": "frações",
    "EF06MA08": "fracionária e decimal",
    "EF06MA09": "fração de uma quantidade",
    "EF06MA10": "adição ou subtração",
    "EF06MA11": "quatro operações",
    "EF06MA13": "porcentagens",
    "EF06MA14": "igualdade",
    "EF06MA16": "plano cartesiano",
    "EF06MA18": "polígonos",
    "EF06MA19": "triângulos",
    "EF06MA20": "quadriláteros",
    "EF06GE08": "mapas",
    "EF06HI06": "rotas de povoamento",
    "EF06HI07": "sociedades antigas",
    "EF06HI08": "astecas",
    "EF06HI09": "Antiguidade Clássica",
    "EF06HI10": "Grécia Antiga",
    "EF06HI11": "Roma Antiga",
    "EF06HI12": "cidadania",
    "EF06HI13": "império",
}

EDGE_NOTES = {
    "conceptual": "Dependência conceitual proposta pela NaEscola. Não é uma ordem obrigatória da BNCC.",
    "cross-subject": "Ligação proposta entre componentes. Não é uma ordem oficial da BNCC.",
    "same-official-code-previous-year": "O mesmo código oficial também se aplica ao ano anterior desta etapa. A BNCC não converte esse recorte em sequência obrigatória de aulas.",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load() -> tuple[dict, dict, dict]:
    return (
        json.loads(BNCC_PATH.read_text(encoding="utf-8")),
        json.loads(STRUCTURE_PATH.read_text(encoding="utf-8")),
        json.loads(COMPUTING_PATH.read_text(encoding="utf-8")),
    )


def line_number(localizador: str | None) -> int:
    if not localizador:
        return 10**9
    match = LINE_RE.search(localizador)
    return int(match.group(1)) if match else 10**9


def topic_id(grade: int, sigla: str, code: str) -> str:
    return f"ef-{grade}-{sigla.lower()}-{code.lower()}"


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def complexity(index: int, total: int) -> str:
    if total <= 1:
        return "introducao"
    ratio = index / (total - 1)
    if ratio < 0.34:
        return "introducao"
    if ratio < 0.67:
        return "desenvolvimento"
    return "consolidacao"


def visuals_for(sigla: str, text: str) -> list[str]:
    found = list(VISUALS[sigla])
    lowered = text.lower()
    if any(word in lowered for word in ("mapa", "cartog", "territór", "territor", "fronteir")):
        if "territory-map" not in found:
            found.append("territory-map")
    if any(word in lowered for word in ("reta numérica", "fração", "frações", "decimal", "número")):
        if sigla == "MA" and "number-line" not in found:
            found.append("number-line")
    if "plano cartesiano" in lowered or "gráfico" in lowered:
        if "function-plot" not in found and sigla == "MA":
            found.append("comparison")
    return found


def unit_key(skill: dict) -> tuple[str, str]:
    org = skill["organizacao"]
    kind = org["tipo"]
    if kind == "campo_pratica":
        return "pratica-de-linguagem", org["pratica_linguagem"]
    if kind == "eixo":
        # English records an eixo and a more specific unidade temática.
        if org.get("unidade_tematica"):
            return "unidade-tematica", org["unidade_tematica"]
        return "eixo", org["eixo"]
    return "unidade-tematica", org["unidade_tematica"]


def context_names(contexts: dict[str, dict]) -> dict[str, str]:
    return {key: value.get("nome", key) for key, value in contexts.items()}


def source_catalog() -> list[dict]:
    return [
        {
            "id": "bncc-2018-pdf",
            "title": "Base Nacional Comum Curricular — Educação Infantil e Ensino Fundamental",
            "authorOrInstitution": "Ministério da Educação (Brasil)",
            "url": "https://basenacionalcomum.mec.gov.br/images/BNCC_EI_EF_110518_versaofinal_site.pdf",
            "identifier": "BNCC 2017/2018",
            "publicationDate": "2017-12-22",
            "accessedAt": "2026-10-28",
            "sourceType": "official-curriculum",
            "relevantClaims": [
                "A BNCC define competências e habilidades do Ensino Fundamental.",
                "A BNCC não estabelece uma sequência única e obrigatória de aulas."
            ],
            "reliabilityNote": "PDF oficial verificado por HTTP 200 em 2026-10-28. Os enunciados das habilidades foram conferidos pelo dataset citado, que aponta página e linha.",
            "license": "Ato oficial brasileiro. A compilação estruturada usada na extração está sob CC BY 4.0.",
        },
        {
            "id": "bncc-dados-2026-07-1",
            "title": "bncc.dev: dados abertos e verificados da BNCC",
            "authorOrInstitution": "Profy",
            "url": "https://doi.org/10.5281/zenodo.21881682",
            "identifier": DATASET_COMMIT,
            "publicationDate": "2026-08-11",
            "accessedAt": "2026-10-28",
            "sourceType": "dataset",
            "relevantClaims": [
                "Estrutura, códigos e enunciados das habilidades usados nesta versão da NaEscola."
            ],
            "reliabilityNote": DATASET_CITATION + f" Commit {DATASET_COMMIT}.",
            "license": "CC BY 4.0",
        },
        {
            "id": "computacao-parecer-2-2022",
            "title": "Parecer CNE/CEB nº 2/2022 — anexo de Computação na educação básica",
            "authorOrInstitution": "Conselho Nacional de Educação / Ministério da Educação",
            "url": "https://github.com/bncc-dev/bncc-dados/blob/9c268978efa2aa250834c6a9edb6074432752838/fontes/anexo-ao-parecer-cneceb-no-2-2022-bncc-computacao.pdf",
            "identifier": "Parecer CNE/CEB nº 2/2022",
            "publicationDate": "2022",
            "accessedAt": "2026-10-28",
            "sourceType": "official-curriculum",
            "relevantClaims": [
                "Normas complementares de Computação na educação básica, distintas do texto da BNCC homologada em 2017."
            ],
            "reliabilityNote": "A cópia arquivada no commit do dataset respondeu HTTP 200. O portal do MEC não foi usado como URL porque não respondeu neste ambiente.",
            "license": "Ato oficial. Cópia de referência redistribuída com o dataset.",
        },
        {
            "id": "cf-1988-art-210",
            "title": "Constituição da República Federativa do Brasil de 1988, artigo 210, §1º",
            "authorOrInstitution": "Assembleia Nacional Constituinte / Presidência da República",
            "url": None,
            "identifier": "CF/1988, art. 210, §1º",
            "publicationDate": "1988-10-05",
            "accessedAt": "2026-10-28",
            "sourceType": "official-curriculum",
            "relevantClaims": [
                "O ensino religioso, de matrícula facultativa, constitui disciplina dos horários normais das escolas públicas de ensino fundamental."
            ],
            "reliabilityNote": "Identificador normativo. A URL do planalto.gov.br não respondeu neste ambiente em 2026-10-28, por isso não foi registrada como link verificado.",
            "license": "Ato oficial.",
        },
    ]


def build_skills_by_code(fundamental: dict, computing: dict) -> dict[str, dict]:
    skills = {item["codigo"]: item for item in fundamental["habilidades"]}
    for item in computing["habilidades_ef"]:
        skills[item["codigo"]] = item
    missing = [code for code in TEXT_CHECKS if code not in skills]
    if missing:
        raise SystemExit(f"Missing expected BNCC codes: {missing}")
    for code, phrase in TEXT_CHECKS.items():
        text = skills[code]["texto"]
        if phrase not in text:
            raise SystemExit(f"Text check failed for {code}: {phrase!r} not in {text}")
    return skills


def stage_for(grade: int) -> tuple[str, str]:
    if grade <= 5:
        return "ef-anos-iniciais", "Ensino Fundamental — Anos Iniciais"
    return "ef-anos-finais", "Ensino Fundamental — Anos Finais"


def make_topic(
    grade: int,
    sigla: str,
    skill: dict,
    names: dict[str, str],
    order: int,
    total: int,
    official_status: str,
) -> dict:
    code = skill["codigo"]
    org = skill.get("organizacao") or {}
    object_ids = skill.get("objetos_conhecimento") or []
    subtopics = [names.get(item, item) for item in object_ids]
    name = " · ".join(subtopics) if subtopics else code
    if len(name) > 180:
        name = name[:177] + "..."
    flags: list[str] = []
    years = list(skill["anos"])
    if len(years) > 1:
        flags.append("multi-year-official-code")
    if any(year not in GRADES for year in years):
        flags.append("official-code-also-covers-years-outside-this-release")
    if sigla == "ER":
        flags.append("matricula-facultativa")
    if official_status == "complemento-computacao-2022":
        flags.append("complemento-2022-nao-e-bncc-2018")
    campos = [names.get(item, item) for item in org.get("campos_atuacao") or []]
    eixo = names.get(org["eixo"], None) if org.get("eixo") else None
    source_id = "bncc-2018-pdf" if skill["documento"] == "bncc-2018" else "computacao-parecer-2-2022"
    return {
        "id": topic_id(grade, sigla, code),
        "slug": slugify(f"{grade}-{sigla}-{code}-{name}"),
        "name": name,
        "summary": skill["texto"],
        "subtopics": subtopics,
        "bnccSkillCodes": [code],
        "skills": [
            {
                "code": code,
                "text": skill["texto"],
                "officialYears": years,
                "placedOnGrade": grade,
                "componentId": skill.get("componente") or "complemento-computacao",
                "documentId": skill["documento"],
                "sourceId": source_id,
                "sourceLocator": skill["fonte"].get("localizador"),
                "pdfLocator": skill["fonte"].get("localizador_pdf"),
            }
        ],
        "learningObjectives": [skill["texto"]],
        "objectiveOrigin": "official-skill-statement",
        "proposedOrder": order,
        "sequenceKind": "naescola-proposed",
        "sequenceBasis": SEQUENCE_BASIS,
        "complexity": complexity(order - 1, total),
        "lessonTypes": LESSON_TYPES[sigla],
        "suggestedVisualizations": visuals_for(sigla, skill["texto"]),
        "prerequisites": [],
        "relatedTopicIds": [],
        "coverageStatus": "planned",
        "flags": flags,
        "camposDeAtuacao": campos,
        "eixo": eixo,
    }


def build_grade(
    grade: int,
    fundamental: dict,
    computing: dict,
    names: dict[str, str],
    components: dict[str, dict],
    areas: dict[str, str],
) -> dict:
    stage_id, stage_label = stage_for(grade)
    grouped: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for skill in fundamental["habilidades"]:
        if grade not in skill["anos"]:
            continue
        sigla = components[skill["componente"]]["sigla_codigo"]
        kind, unit_id = unit_key(skill)
        grouped[sigla][(kind, unit_id)].append(skill)
    for skill in computing["habilidades_ef"]:
        if grade not in skill["anos"]:
            continue
        eixo_id = skill["eixo"]
        grouped["CO"][("eixo", eixo_id)].append(skill)

    subjects = []
    for sigla in SUBJECT_ORDER:
        units_map = grouped.get(sigla)
        if not units_map:
            continue
        if sigla == "CO":
            component_id = "complemento-computacao"
            area_id = "complemento-computacao-2022"
            area_name = "Computação (complemento de 2022)"
            official_status = "complemento-computacao-2022"
            name = "Computação"
            local_note = DESCRIPTIONS["CO"]
        else:
            component = next(item for item in components.values() if item["sigla_codigo"] == sigla and item["etapa"] == "EF")
            component_id = component["id"]
            area_id = component["area"]
            area_name = areas[area_id]
            official_status = "bncc-2018"
            name = component["nome"]
            local_note = DESCRIPTIONS["ER"] if sigla == "ER" else None
        units = []
        for (kind, unit_id), skills in units_map.items():
            skills.sort(key=lambda item: (line_number(item["fonte"].get("localizador")), item["codigo"]))
            topics = [
                make_topic(grade, sigla, skill, names, index, len(skills), official_status)
                for index, skill in enumerate(skills, start=1)
            ]
            for previous, current in zip(topics, topics[1:]):
                previous["relatedTopicIds"].append(current["id"])
                current["relatedTopicIds"].append(previous["id"])
            units.append(
                {
                    "id": f"ef-{grade}-{sigla.lower()}-{slugify(unit_id)}",
                    "sourceId": unit_id,
                    "name": names.get(unit_id, unit_id),
                    "kind": kind,
                    "official": True,
                    "sequenceKind": "document-order-adopted-as-naescola-proposal",
                    "topics": topics,
                }
            )
        units.sort(key=lambda unit: line_number(unit["topics"][0]["skills"][0]["sourceLocator"]))
        subjects.append(
            {
                "id": f"ef-{grade}-{sigla.lower()}",
                "slug": slugify(name),
                "name": name,
                "componentId": component_id,
                "codeSigla": sigla,
                "areaId": area_id,
                "areaName": area_name,
                "description": DESCRIPTIONS[sigla],
                "officialStatus": official_status,
                "localDependencyNote": local_note,
                "units": units,
            }
        )
    omissions = []
    if grade < 6:
        omissions.append(
            {
                "component": "Língua Inglesa",
                "reason": "A BNCC introduz Língua Inglesa a partir do 6º ano. Não há habilidades oficiais desse componente para este ano.",
            }
        )
    notes = [
        "As habilidades são oficiais. A ordem dentro de cada componente é uma proposta da NaEscola baseada na ordem do documento, não uma sequência obrigatória da BNCC.",
        "Códigos de bloco de anos (como EF15, EF35 ou EF67) permanecem com o texto e o recorte oficiais. Quando aparecem em mais de um ano desta entrega, a repetição indica o recorte oficial, não uma habilidade nova.",
        "O 7º, o 8º e o 9º anos não foram pesquisados nesta entrega. Códigos oficiais que também valem para esses anos estão sinalizados.",
    ]
    return {
        "schemaVersion": "1.0.0",
        "gradeId": f"ef-{grade}",
        "gradeNumber": grade,
        "gradeLabel": f"{grade}º ano",
        "stageId": stage_id,
        "stageLabel": stage_label,
        "nomenclatureNote": "Nomenclatura atual do Ensino Fundamental. Não usamos 'série' na interface.",
        "subjects": subjects,
        "omissions": omissions,
        "sources": source_catalog(),
        "notes": notes,
    }


def iter_topics(grade_doc: dict):
    for subject in grade_doc["subjects"]:
        for unit in subject["units"]:
            for topic in unit["topics"]:
                yield subject, unit, topic


def index_topics(grades: dict[int, dict]) -> dict[str, dict]:
    index = {}
    for grade, doc in grades.items():
        for _subject, _unit, topic in iter_topics(doc):
            code = topic["bnccSkillCodes"][0]
            index.setdefault(code, []).append((grade, topic))
    return index


def apply_links(grades: dict[int, dict], skills: dict[str, dict]) -> dict:
    indexed = index_topics(grades)
    for code, placements in indexed.items():
        placements.sort()
        for (grade, topic), (previous_grade, previous) in zip(placements[1:], placements):
            if previous_grade != grade - 1:
                continue
            if any(item["topicId"] == previous["id"] for item in topic["prerequisites"]):
                continue
            topic["prerequisites"].append(
                {
                    "topicId": previous["id"],
                    "kind": "same-official-code-previous-year",
                    "note": EDGE_NOTES["same-official-code-previous-year"],
                }
            )
    resolved = 0
    for dependent, prerequisite, kind in CONCEPTUAL_EDGES:
        if dependent not in skills or prerequisite not in skills:
            raise SystemExit(f"Unknown edge {dependent} -> {prerequisite}")
        dependent_grade = min(year for year in skills[dependent]["anos"] if year in GRADES)
        prerequisite_grade = min(year for year in skills[prerequisite]["anos"] if year in GRADES)
        dependent_topic = next(topic for grade, topic in indexed[dependent] if grade == dependent_grade)
        prerequisite_topic = next(topic for grade, topic in indexed[prerequisite] if grade == prerequisite_grade)
        if any(item["topicId"] == prerequisite_topic["id"] for item in dependent_topic["prerequisites"]):
            continue
        dependent_topic["prerequisites"].append(
            {
                "topicId": prerequisite_topic["id"],
                "kind": kind,
                "note": EDGE_NOTES[kind],
            }
        )
        resolved += 1
    return {"conceptualEdgesResolved": resolved}


def detect_cycles(grades: dict[int, dict]) -> list[list[str]]:
    graph: dict[str, list[str]] = {}
    for doc in grades.values():
        for _s, _u, topic in iter_topics(doc):
            graph[topic["id"]] = [item["topicId"] for item in topic["prerequisites"]]
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
            if nxt not in graph:
                continue
            walk(nxt, stack + [nxt])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        walk(node, [node])
    return cycles


def broken_references(grades: dict[int, dict]) -> list[str]:
    ids = {topic["id"] for doc in grades.values() for _s, _u, topic in iter_topics(doc)}
    broken = []
    for doc in grades.values():
        for _s, _u, topic in iter_topics(doc):
            for link in topic["prerequisites"]:
                if link["topicId"] not in ids:
                    broken.append(f"{topic['id']} -> {link['topicId']}")
            for related in topic["relatedTopicIds"]:
                if related not in ids:
                    broken.append(f"{topic['id']} related {related}")
    return broken


def duplicate_ids(grades: dict[int, dict]) -> list[str]:
    seen = set()
    duplicates = []
    for doc in grades.values():
        for subject in doc["subjects"]:
            if subject["id"] in seen:
                duplicates.append(subject["id"])
            seen.add(subject["id"])
            for unit in subject["units"]:
                if unit["id"] in seen:
                    duplicates.append(unit["id"])
                seen.add(unit["id"])
                for topic in unit["topics"]:
                    if topic["id"] in seen:
                        duplicates.append(topic["id"])
                    seen.add(topic["id"])
    return duplicates


def count_expected(fundamental: dict, computing: dict) -> dict[str, int]:
    counts = {str(grade): 0 for grade in GRADES}
    for skill in fundamental["habilidades"]:
        for grade in skill["anos"]:
            if grade in GRADES:
                counts[str(grade)] += 1
    for skill in computing["habilidades_ef"]:
        for grade in skill["anos"]:
            if grade in GRADES:
                counts[str(grade)] += 1
    return counts


def write_markdown(grades: dict[int, dict], report: dict) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Currículo dos 3º, 4º, 5º e 6º anos",
        "",
        "Este texto é gerado por `scripts/build_curriculum.py`. Não edite os números à mão.",
        "",
        "## O que é oficial e o que é proposta",
        "",
        "- Oficial: competências, habilidades, unidades, objetos de conhecimento, campos e práticas, com o código e o enunciado da fonte.",
        "- Proposta da NaEscola: ordem de ensino, complexidade estimada, tipos de aula, visualizações sugeridas e pré-requisitos.",
        "- A BNCC não é tratada como uma lista obrigatória de aulas.",
        "",
        "## Fontes",
        "",
        f"- BNCC, PDF do MEC, consultado em 2026-10-28.",
        f"- Dataset bncc-dados `{DATASET_VERSION}`, commit `{DATASET_COMMIT}`.",
        "- Parecer CNE/CEB nº 2/2022 para Computação, em cópia arquivada no mesmo commit.",
        "- Constituição de 1988, art. 210, §1º, citada por identificador. A URL do Planalto não respondeu neste ambiente.",
        "",
        "## Contagens",
        "",
        f"- Habilidades oficiais distintas que incidem nos anos 3 a 6, incluindo Computação: {report['uniqueSkills']}.",
        f"- Colocações ano-habilidade: {report['placements']}.",
        f"- Pré-requisitos conceituais ou entre componentes: {report['conceptualEdgesResolved']}.",
        f"- Arestas de continuidade do mesmo código: {report['continuityEdges']}.",
        f"- Ciclos: {report['cycles']}. Referências quebradas: {report['brokenReferences']}. IDs duplicados: {report['duplicateIds']}.",
        "",
        "## Lacunas deliberadas",
        "",
        "- 1º, 2º, 7º, 8º e 9º anos não foram montados.",
        "- Ensino Infantil, Ensino Médio e Ensino Superior não têm habilidades nesta entrega.",
        "- Currículos estaduais e municipais não foram comparados um a um.",
        "- A ordem proposta não foi validada por uma rede de ensino.",
        "",
    ]
    for grade, doc in grades.items():
        lines.append(f"## {doc['gradeLabel']} — {doc['stageLabel']}")
        lines.append("")
        for omission in doc["omissions"]:
            lines.append(f"- Omissão explícita: {omission['component']}. {omission['reason']}")
        for subject in doc["subjects"]:
            topic_count = sum(len(unit["topics"]) for unit in subject["units"])
            status = "BNCC 2018" if subject["officialStatus"] == "bncc-2018" else "complemento de 2022"
            lines.append(f"### {subject['name']} ({status}) — {topic_count} habilidades")
            lines.append("")
            lines.append(subject["description"])
            lines.append("")
            if subject["localDependencyNote"] and subject["codeSigla"] != "CO":
                lines.append(subject["localDependencyNote"])
                lines.append("")
            for unit in subject["units"]:
                lines.append(f"- {unit['name']} ({unit['kind']}): {len(unit['topics'])} habilidades")
        lines.append("")
        path = DOCS_DIR / f"grade-{grade}.md"
        section = [f"# {doc['gradeLabel']}", "", doc["nomenclatureNote"], ""]
        section.extend([line for line in lines if line.startswith("###") or line.startswith("- ") or line.startswith("Omissão")][-0:])
        # Write a focused grade file from this document only.
        grade_lines = [
            f"# {doc['gradeLabel']}",
            "",
            doc["stageLabel"] + ". " + doc["nomenclatureNote"],
            "",
            "A ordem abaixo é a sequência proposta pela NaEscola. Os códigos e os enunciados são oficiais.",
            "",
        ]
        for omission in doc["omissions"]:
            grade_lines.append(f"Omissão explícita: **{omission['component']}**. {omission['reason']}")
            grade_lines.append("")
        for subject in doc["subjects"]:
            grade_lines.append(f"## {subject['name']}")
            grade_lines.append("")
            grade_lines.append(f"Estado oficial: `{subject['officialStatus']}`. Área: {subject['areaName']}.")
            grade_lines.append("")
            grade_lines.append(subject["description"])
            grade_lines.append("")
            if subject["localDependencyNote"]:
                grade_lines.append(subject["localDependencyNote"])
                grade_lines.append("")
            for unit in subject["units"]:
                grade_lines.append(f"### {unit['name']}")
                grade_lines.append("")
                for topic in unit["topics"]:
                    skill = topic["skills"][0]
                    years = ", ".join(str(year) for year in skill["officialYears"])
                    grade_lines.append(
                        f"- `{skill['code']}` (anos oficiais: {years}) — {skill['text']}"
                    )
                grade_lines.append("")
        path.write_text("\n".join(grade_lines), encoding="utf-8")
    (DOCS_DIR / "overview.md").write_text("\n".join(lines), encoding="utf-8")


def competencies(structure: dict) -> dict:
    generals = []
    for item in structure["competencias_gerais"]:
        generals.append(
            {
                "id": item["id"],
                "number": item["numero"],
                "text": item["texto"],
                "sourceLocator": item["fonte"].get("localizador"),
                "pdfLocator": item["fonte"].get("localizador_pdf"),
                "origin": "bncc-2018",
            }
        )
    specific = []
    for item in structure["competencias_especificas"]:
        area = item.get("area") or ""
        component = item.get("componente") or ""
        if not (area.startswith("ef-") or component.startswith("ef-")):
            continue
        specific.append(
            {
                "id": item["id"],
                "number": item["numero"],
                "text": item["texto"],
                "kind": item["tipo"],
                "areaId": item.get("area"),
                "componentId": item.get("componente"),
                "sourceLocator": item["fonte"].get("localizador"),
                "pdfLocator": item["fonte"].get("localizador_pdf"),
                "origin": "bncc-2018",
            }
        )
    return {
        "schemaVersion": "1.0.0",
        "note": "Competências oficiais da BNCC. Não são aulas e não têm ordem de ensino proposta.",
        "general": generals,
        "specificFundamental": specific,
        "sourceId": "bncc-2018-pdf",
    }


def main() -> None:
    fundamental, structure, computing = load()
    skills = build_skills_by_code(fundamental, computing)
    contexts = {item["id"]: item for item in fundamental["contextos_organizacao"]}
    for eixo in computing["eixos"]:
        contexts[eixo["id"]] = eixo
    for obj in computing["objetos_conhecimento"]:
        contexts[obj["id"]] = obj
    names = context_names(contexts)
    components = {item["id"]: item for item in structure["componentes_curriculares"]}
    areas = {item["id"]: item["nome"] for item in structure["areas_conhecimento"]}
    grades = {
        grade: build_grade(grade, fundamental, computing, names, components, areas)
        for grade in GRADES
    }
    link_report = apply_links(grades, skills)
    cycles = detect_cycles(grades)
    broken = broken_references(grades)
    duplicates = duplicate_ids(grades)
    if cycles or broken or duplicates:
        raise SystemExit(
            json.dumps({"cycles": cycles[:5], "broken": broken[:10], "duplicates": duplicates[:10]}, ensure_ascii=False)
        )
    expected = count_expected(fundamental, computing)
    actual = {}
    unique_codes = set()
    placements = 0
    continuity = 0
    for grade, doc in grades.items():
        count = 0
        for _s, _u, topic in iter_topics(doc):
            count += 1
            placements += 1
            unique_codes.add(topic["bnccSkillCodes"][0])
            continuity += sum(1 for item in topic["prerequisites"] if item["kind"] == "same-official-code-previous-year")
        actual[str(grade)] = count
        if count != expected[str(grade)]:
            raise SystemExit(f"Grade {grade} has {count} topics, expected {expected[str(grade)]}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for grade, doc in grades.items():
        (OUT_DIR / f"grade-{grade}.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    comp = competencies(structure)
    (OUT_DIR / "competencies.json").write_text(json.dumps(comp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "schemaVersion": "1.0.0",
        "datasetCommit": DATASET_COMMIT,
        "datasetVersion": DATASET_VERSION,
        "sourceSha256": {
            "ensino-fundamental.json": sha256(BNCC_PATH),
            "estrutura.json": sha256(STRUCTURE_PATH),
            "computacao.json": sha256(COMPUTING_PATH),
        },
        "grades": actual,
        "uniqueSkills": len(unique_codes),
        "placements": placements,
        "generalCompetencies": len(comp["general"]),
        "specificCompetencies": len(comp["specificFundamental"]),
        "conceptualEdgesResolved": link_report["conceptualEdgesResolved"],
        "continuityEdges": continuity,
        "cycles": len(cycles),
        "brokenReferences": len(broken),
        "duplicateIds": len(duplicates),
        "mapDatasetCommitNotUsedHere": MAP_COMMIT,
    }
    (OUT_DIR / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(grades, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
