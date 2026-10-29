"""Educação Infantil, Ensino Médio, and the three séries.

Official statements are copied from the pinned dataset. Age-group columns
and the absence of Ensino Médio seriation were checked against the 600-page
PDF archived in the same dataset commit. Teaching order and prerequisite
links are NaEscola proposals.
"""

from __future__ import annotations

import re
from collections import defaultdict

LINE_RE = re.compile(r"linha\s+(\d+)", re.IGNORECASE)
SEQUENCE_BASIS_EI = (
    "Ordem dos objetivos no quadro oficial do campo, adotada como sequência proposta "
    "pela NaEscola. A numeração não é uma ordem obrigatória de aulas."
)
SEQUENCE_BASIS_EM = (
    "Ordem de apresentação no documento oficial, adotada como sequência proposta "
    "pela NaEscola. A BNCC não indica a série destas habilidades e não define "
    "esta ordem como sequência obrigatória de aulas."
)
AGE_GROUP_NOTE = (
    "A BNCC apresenta estes objetivos na mesma linha do quadro, em faixas etárias sucessivas. "
    "A NaEscola trata a faixa anterior como pré-requisito proposto. Isso não é uma ordem obrigatória de aulas."
)
FULL_PDF_URL = (
    "https://github.com/bncc-dev/bncc-dados/blob/9c268978efa2aa250834c6a9edb6074432752838/"
    "fontes/Base-Nacional-Comum-Curricular-BNCC.pdf"
)

GROUPS = (
    {
        "id": "ei-bebes",
        "number": 1,
        "sourceId": "ei-grupo-01",
        "label": "Bebês",
        "span": "Bebês (0–1a6m)",
        "note": "Grupo etário da BNCC, não um ano escolar. A faixa vai de zero a 1 ano e 6 meses.",
    },
    {
        "id": "ei-bem-pequenas",
        "number": 2,
        "sourceId": "ei-grupo-02",
        "label": "Crianças bem pequenas",
        "span": "Crianças bem pequenas (1a7m–3a11m)",
        "note": "Grupo etário da BNCC, não um ano escolar. A faixa vai de 1 ano e 7 meses a 3 anos e 11 meses.",
    },
    {
        "id": "ei-pequenas",
        "number": 3,
        "sourceId": "ei-grupo-03",
        "label": "Crianças pequenas",
        "span": "Crianças pequenas (4a–5a11m)",
        "note": "Grupo etário da BNCC para a pré-escola: 4 anos a 5 anos e 11 meses. Não é um ano escolar numerado.",
    },
)

# Transcribed from the archived PDF, page 40 (printed page 38), on 2026-10-29.
# Line-break hyphens in planejamento, diferentes, questionamentos, and constituindo were joined.
RIGHTS = (
    (
        "ei-direito-conviver",
        "Conviver",
        "Conviver com outras crianças e adultos, em pequenos e grandes grupos, utilizando diferentes linguagens, ampliando o conhecimento de si e do outro, o respeito em relação à cultura e às diferenças entre as pessoas.",
    ),
    (
        "ei-direito-brincar",
        "Brincar",
        "Brincar cotidianamente de diversas formas, em diferentes espaços e tempos, com diferentes parceiros (crianças e adultos), ampliando e diversificando seu acesso a produções culturais, seus conhecimentos, sua imaginação, sua criatividade, suas experiências emocionais, corporais, sensoriais, expressivas, cognitivas, sociais e relacionais.",
    ),
    (
        "ei-direito-participar",
        "Participar",
        "Participar ativamente, com adultos e outras crianças, tanto do planejamento da gestão da escola e das atividades propostas pelo educador quanto da realização das atividades da vida cotidiana, tais como a escolha das brincadeiras, dos materiais e dos ambientes, desenvolvendo diferentes linguagens e elaborando conhecimentos, decidindo e se posicionando.",
    ),
    (
        "ei-direito-explorar",
        "Explorar",
        "Explorar movimentos, gestos, sons, formas, texturas, cores, palavras, emoções, transformações, relacionamentos, histórias, objetos, elementos da natureza, na escola e fora dela, ampliando seus saberes sobre a cultura, em suas diversas modalidades: as artes, a escrita, a ciência e a tecnologia.",
    ),
    (
        "ei-direito-expressar",
        "Expressar",
        "Expressar, como sujeito dialógico, criativo e sensível, suas necessidades, emoções, sentimentos, dúvidas, hipóteses, descobertas, opiniões, questionamentos, por meio de diferentes linguagens.",
    ),
    (
        "ei-direito-conhecer-se",
        "Conhecer-se",
        "Conhecer-se e construir sua identidade pessoal, social e cultural, constituindo uma imagem positiva de si e de seus grupos de pertencimento, nas diversas experiências de cuidados, interações, brincadeiras e linguagens vivenciadas na instituição escolar e em seu contexto familiar e comunitário.",
    ),
)

EMPTY_COMPONENTS = (
    ("em-comp-arte", "AR", "Arte", "em-area-lgg", "Linguagens e suas Tecnologias"),
    ("em-comp-educacao-fisica", "EF", "Educação Física", "em-area-lgg", "Linguagens e suas Tecnologias"),
    ("em-comp-lingua-inglesa", "LI", "Língua Inglesa", "em-area-lgg", "Linguagens e suas Tecnologias"),
    ("em-comp-biologia", "BI", "Biologia", "em-area-cnt", "Ciências da Natureza e suas Tecnologias"),
    ("em-comp-fisica", "FI", "Física", "em-area-cnt", "Ciências da Natureza e suas Tecnologias"),
    ("em-comp-quimica", "QI", "Química", "em-area-cnt", "Ciências da Natureza e suas Tecnologias"),
    ("em-comp-historia", "HI", "História", "em-area-chs", "Ciências Humanas e Sociais Aplicadas"),
    ("em-comp-geografia", "GE", "Geografia", "em-area-chs", "Ciências Humanas e Sociais Aplicadas"),
    ("em-comp-sociologia", "SO", "Sociologia", "em-area-chs", "Ciências Humanas e Sociais Aplicadas"),
    ("em-comp-filosofia", "FL", "Filosofia", "em-area-chs", "Ciências Humanas e Sociais Aplicadas"),
)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def line_number(localizador: str | None) -> int:
    if not localizador:
        return 10**9
    match = LINE_RE.search(localizador)
    return int(match.group(1)) if match else 10**9


def complexity(index: int, total: int) -> str:
    if total <= 1:
        return "introducao"
    ratio = index / (total - 1)
    if ratio < 0.34:
        return "introducao"
    if ratio < 0.67:
        return "desenvolvimento"
    return "consolidacao"


def display_name(text: str) -> tuple[str, list[str]]:
    compact = " ".join(text.split())
    if len(compact) <= 180:
        return compact, []
    return compact[:177] + "...", ["rotulo-abreviado-do-enunciado-oficial"]


def full_pdf_source() -> dict:
    return {
        "id": "bncc-2018-pdf-completo",
        "title": "Base Nacional Comum Curricular — versão completa arquivada (600 páginas)",
        "authorOrInstitution": "Ministério da Educação (Brasil)",
        "url": FULL_PDF_URL,
        "identifier": "bncc-dados:9c268978efa2aa250834c6a9edb6074432752838:fontes/Base-Nacional-Comum-Curricular-BNCC.pdf",
        "publicationDate": "2018-12-14",
        "accessedAt": "2026-10-29",
        "sourceType": "official-curriculum",
        "relevantClaims": [
            "A Educação Infantil organiza objetivos em três faixas etárias e cinco campos de experiências.",
            "A numeração sequencial das habilidades do Ensino Fundamental não representa uma ordem obrigatória.",
            "As habilidades do Ensino Médio são apresentadas sem indicação de seriação.",
        ],
        "reliabilityNote": (
            "Cópia de 600 páginas no commit do dataset. Em 2026-10-29 foram lidas a página PDF 34 "
            "(sem seriação), a página PDF 40 (direitos de aprendizagem) e trechos dos quadros da "
            "Educação Infantil e de EM13CHS101. O PDF curto BNCC_EI_EF não foi usado como fonte do Ensino Médio."
        ),
        "license": "Ato oficial brasileiro, em cópia arquivada com o dataset.",
    }


def stage_sources(base_sources: list[dict]) -> list[dict]:
    kept = [item for item in base_sources if item["id"] != "bncc-2018-pdf"]
    return [full_pdf_source(), *kept]


def uncertainties() -> list[str]:
    return [
        "Currículos estaduais e municipais não foram comparados.",
        "A ordem proposta não foi validada por uma rede de ensino.",
        "O portal do Planalto não respondeu em 2026-10-29. Leis são citadas por identificador e pela ementa do recorte marcos-legais, sem URL verificada nesta sessão.",
    ]


def lesson_types(sigla: str) -> list[str]:
    return {
        "LP": ["explicacao", "exemplos", "pratica"],
        "LGG": ["explicacao", "apreciacao", "pratica"],
        "MA": ["explicacao", "exemplos", "pratica"],
        "CNT": ["explicacao", "observacao", "pratica"],
        "CHS": ["explicacao", "linha-do-tempo", "fontes"],
        "CO": ["explicacao", "exemplo-passo-a-passo", "pratica"],
        "EO": ["explicacao", "brincadeira"],
        "CG": ["explicacao", "brincadeira"],
        "TS": ["explicacao", "apreciacao", "pratica"],
        "EF": ["explicacao", "brincadeira"],
        "ET": ["explicacao", "observacao", "pratica"],
    }.get(sigla, ["explicacao"])


def visuals(sigla: str) -> list[str]:
    return {
        "MA": ["number-line", "comparison"],
        "CNT": ["state-steps", "comparison"],
        "CHS": ["event-timeline"],
        "CO": ["state-steps", "comparison"],
        "ET": ["comparison"],
    }.get(sigla, ["comparison"])


def skill_record(
    code: str,
    text: str,
    years: list[int],
    placed_on: int,
    component_id: str,
    document_id: str,
    source_id: str,
    fonte: dict,
    span: str | None,
) -> dict:
    return {
        "code": code,
        "text": text,
        "officialYears": years,
        "placedOnGrade": placed_on,
        "componentId": component_id,
        "documentId": document_id,
        "sourceId": source_id,
        "sourceLocator": fonte.get("localizador"),
        "pdfLocator": fonte.get("localizador_pdf"),
        "officialSpanLabel": span,
    }


def make_learning_topic(
    *,
    topic_id: str,
    sigla: str,
    code: str,
    text: str,
    subtopics: list[str],
    order: int,
    total: int,
    skill: dict,
    flags: list[str],
    origin: str,
    basis: str,
    campos: list[str],
    eixo: str | None,
    competency_ids: list[str],
) -> dict:
    name, name_flags = display_name(text)
    return {
        "id": topic_id,
        "slug": slugify(topic_id),
        "name": name,
        "summary": text,
        "subtopics": subtopics,
        "bnccSkillCodes": [code],
        "skills": [skill],
        "learningObjectives": [text],
        "objectiveOrigin": origin,
        "proposedOrder": order,
        "sequenceKind": "naescola-proposed",
        "sequenceBasis": basis,
        "complexity": complexity(order - 1, total),
        "lessonTypes": lesson_types(sigla),
        "suggestedVisualizations": visuals(sigla),
        "prerequisites": [],
        "relatedTopicIds": [],
        "coverageStatus": "planned",
        "flags": flags + name_flags,
        "camposDeAtuacao": campos,
        "eixo": eixo,
        "officialCompetencyIds": competency_ids,
    }


def link_neighbors(topics: list[dict]) -> None:
    for previous, current in zip(topics, topics[1:]):
        previous["relatedTopicIds"].append(current["id"])
        current["relatedTopicIds"].append(previous["id"])


def finish_units(units: list[dict]) -> list[dict]:
    units.sort(key=lambda unit: line_number(unit["topics"][0]["skills"][0]["sourceLocator"]) if unit["topics"] else 10**9)
    return units


def build_early_childhood(infantil: dict, structure: dict, computing: dict, base_sources: list[dict]) -> list[dict]:
    campos = {item["id"]: item["nome"] for item in structure["campos_experiencias"]}
    campo_order = [item["id"] for item in structure["campos_experiencias"]]
    eixos = {item["id"]: item["nome"] for item in computing["eixos"]}
    by_group: dict[str, list[dict]] = defaultdict(list)
    for objective in infantil["objetivos"]:
        by_group[objective["grupo_etario"]].append(objective)
    computing_by_group: dict[str, list[dict]] = defaultdict(list)
    for objective in computing["objetivos_ei"]:
        computing_by_group[objective["grupo_etario"]].append(objective)
    documents = []
    for group in GROUPS:
        subjects = []
        for campo_id in campo_order:
            objectives = [item for item in by_group[group["sourceId"]] if item["campo_experiencias"] == campo_id]
            objectives.sort(key=lambda item: item["codigo"])
            sigla = campo_id.removeprefix("ei-campo-").upper()
            topics = []
            for index, objective in enumerate(objectives, start=1):
                topics.append(
                    make_learning_topic(
                        topic_id=f"{group['id']}-{objective['codigo'].lower()}",
                        sigla=sigla,
                        code=objective["codigo"],
                        text=objective["texto"],
                        subtopics=[],
                        order=index,
                        total=len(objectives),
                        skill=skill_record(
                            objective["codigo"],
                            objective["texto"],
                            [group["number"]],
                            group["number"],
                            campo_id,
                            objective["documento"],
                            "bncc-2018-pdf-completo",
                            objective["fonte"],
                            group["span"],
                        ),
                        flags=["grupo-etario-oficial"],
                        origin="official-learning-objective",
                        basis=SEQUENCE_BASIS_EI,
                        campos=[campos[campo_id]],
                        eixo=None,
                        competency_ids=[],
                    )
                )
            link_neighbors(topics)
            subjects.append(
                {
                    "id": f"{group['id']}-{sigla.lower()}",
                    "slug": slugify(campos[campo_id]),
                    "name": campos[campo_id],
                    "componentId": campo_id,
                    "codeSigla": sigla,
                    "areaId": "educacao-infantil",
                    "areaName": "Educação Infantil",
                    "description": "Campo de experiências da BNCC. Os objetivos abaixo são oficiais; a ordem é proposta da NaEscola.",
                    "officialStatus": "bncc-2018",
                    "localDependencyNote": None,
                    "units": [
                        {
                            "id": f"{group['id']}-{sigla.lower()}-objetivos",
                            "sourceId": campo_id,
                            "name": campos[campo_id],
                            "kind": "campo-de-experiencia",
                            "official": True,
                            "sequenceKind": "document-order-adopted-as-naescola-proposal",
                            "officialText": None,
                            "topics": topics,
                        }
                    ],
                }
            )
        computing_items = computing_by_group.get(group["sourceId"], [])
        if computing_items:
            by_eixo: dict[str, list[dict]] = defaultdict(list)
            for item in computing_items:
                by_eixo[item["eixo"]].append(item)
            units = []
            for eixo_id, items in by_eixo.items():
                items.sort(key=lambda item: (line_number(item["fonte"].get("localizador")), item["codigo"]))
                topics = []
                for index, item in enumerate(items, start=1):
                    topics.append(
                        make_learning_topic(
                            topic_id=f"{group['id']}-{item['codigo'].lower()}",
                            sigla="CO",
                            code=item["codigo"],
                            text=item["texto"],
                            subtopics=[],
                            order=index,
                            total=len(items),
                            skill=skill_record(
                                item["codigo"],
                                item["texto"],
                                [group["number"]],
                                group["number"],
                                "complemento-computacao",
                                item["documento"],
                                "computacao-parecer-2-2022",
                                item["fonte"],
                                group["span"],
                            ),
                            flags=["complemento-2022-nao-e-bncc-2018", "grupo-etario-oficial"],
                            origin="official-learning-objective",
                            basis=SEQUENCE_BASIS_EI,
                            campos=[],
                            eixo=eixos[eixo_id],
                            competency_ids=[],
                        )
                    )
                link_neighbors(topics)
                units.append(
                    {
                        "id": f"{group['id']}-co-{slugify(eixo_id)}",
                        "sourceId": eixo_id,
                        "name": eixos[eixo_id],
                        "kind": "eixo",
                        "official": True,
                        "sequenceKind": "document-order-adopted-as-naescola-proposal",
                        "officialText": None,
                        "topics": topics,
                    }
                )
            subjects.append(
                {
                    "id": f"{group['id']}-co",
                    "slug": "computacao",
                    "name": "Computação",
                    "componentId": "complemento-computacao",
                    "codeSigla": "CO",
                    "areaId": "complemento-computacao-2022",
                    "areaName": "Computação (complemento de 2022)",
                    "description": "Complemento de Computação do Parecer CNE/CEB nº 2/2022. No anexo, os objetivos da Educação Infantil estão na pré-escola. Não fazem parte do texto homologado da BNCC de 2018.",
                    "officialStatus": "complemento-computacao-2022",
                    "localDependencyNote": "Complemento de 2022, não uma habilidade da BNCC de 2018.",
                    "units": finish_units(units),
                }
            )
        documents.append(
            {
                "schemaVersion": "1.0.0",
                "gradeId": group["id"],
                "gradeNumber": group["number"],
                "gradeLabel": group["label"],
                "stageId": "educacao-infantil",
                "stageLabel": "Educação Infantil",
                "nomenclatureNote": group["note"],
                "segmentKind": "grupo-etario",
                "skillPlacement": "official-age-group",
                "officialSkillCatalogId": None,
                "subjects": subjects,
                "omissions": [
                    {
                        "component": "Ensino Religioso",
                        "reason": "Não há campo de Ensino Religioso na BNCC da Educação Infantil. A Constituição, art. 210, §1º, situa o ensino religioso no ensino fundamental.",
                    },
                    {
                        "component": "Língua Inglesa",
                        "reason": "A BNCC não define habilidades de Língua Inglesa na Educação Infantil.",
                    },
                ],
                "sources": stage_sources(base_sources),
                "notes": [
                    "Os objetivos de aprendizagem e desenvolvimento são oficiais. A ordem em cada campo é uma proposta da NaEscola.",
                    "Os seis direitos de aprendizagem pertencem à etapa. Este arquivo não atribui um direito a cada objetivo, porque a BNCC não faz esse vínculo por código.",
                    "Creche e pré-escola não são três anos numerados. Bebês e crianças bem pequenas cabem na creche; crianças pequenas correspondem à pré-escola.",
                ],
                "uncertainties": uncertainties()
                + [
                    "A relação entre cada objetivo e os direitos de aprendizagem não está codificada na fonte usada aqui.",
                ],
            }
        )
    return documents


def apply_age_group_links(documents: list[dict], infantil: dict) -> int:
    index = {}
    for doc in documents:
        for subject in doc["subjects"]:
            for unit in subject["units"]:
                for topic in unit["topics"]:
                    index[topic["bnccSkillCodes"][0]] = topic
    linked = 0
    for alignment in infantil["alinhamentos"]:
        codes = alignment["objetivos"]
        for earlier, later in zip(codes, codes[1:]):
            if earlier not in index or later not in index:
                raise SystemExit(f"Age-group alignment is missing a code: {alignment['id']}")
            topic = index[later]
            prerequisite = index[earlier]
            topic["prerequisites"].append(
                {
                    "topicId": prerequisite["id"],
                    "kind": "same-objective-previous-age-group",
                    "note": AGE_GROUP_NOTE,
                }
            )
            linked += 1
    return linked


def competency_map(structure: dict, computing: dict) -> dict[str, dict]:
    found = {item["id"]: item for item in structure["competencias_especificas"]}
    for item in computing["competencias"]:
        found[item["id"]] = item
    return found


def build_high_school(medio: dict, structure: dict, computing: dict, base_sources: list[dict]) -> dict:
    areas = {item["id"]: item["nome"] for item in structure["areas_conhecimento"]}
    competencies = competency_map(structure, computing)
    contexts = {item["id"]: item["nome"] for item in medio["contextos_organizacao"]}
    subjects: list[dict] = []

    def add_subject(subject: dict) -> None:
        subjects.append(subject)

    def grouped_subject(
        *,
        subject_id: str,
        name: str,
        sigla: str,
        component_id: str,
        area_id: str,
        description: str,
        official_status: str,
        local_note: str | None,
        groups: dict[tuple[str, str, str | None], list[dict]],
    ) -> None:
        units = []
        for (kind, source_id, official_text), items in groups.items():
            items.sort(key=lambda item: (line_number(item["fonte"].get("localizador")), item["codigo"]))
            topics = []
            for index, item in enumerate(items, start=1):
                competency_ids = list(item.get("competencias_especificas") or [])
                if item.get("competencia"):
                    competency_ids = [item["competencia"]]
                flags = ["sem-seriacao-oficial", "colocacao-na-etapa-nao-e-serie"]
                basis = SEQUENCE_BASIS_EM
                if len(competency_ids) > 1:
                    flags.append("tambem-vinculada-a-outras-competencias")
                    basis += (
                        " Esta habilidade oficial lista mais de uma competência. "
                        "A unidade usa a primeira da fonte, o que é uma escolha de organização da NaEscola."
                    )
                if official_status != "bncc-2018":
                    flags.append("complemento-2022-nao-e-bncc-2018")
                campos = [contexts[campo] for campo in (item.get("campos_atuacao_social") or []) if campo in contexts]
                topics.append(
                    make_learning_topic(
                        topic_id=f"em-etapa-{item['codigo'].lower()}",
                        sigla=sigla,
                        code=item["codigo"],
                        text=item["texto"],
                        subtopics=campos,
                        order=index,
                        total=len(items),
                        skill=skill_record(
                            item["codigo"],
                            item["texto"],
                            [],
                            0,
                            component_id,
                            item["documento"],
                            "bncc-2018-pdf-completo" if item["documento"] == "bncc-2018" else "computacao-parecer-2-2022",
                            item["fonte"],
                            "Ensino Médio, sem série oficial",
                        ),
                        flags=flags,
                        origin="official-skill-statement",
                        basis=basis,
                        campos=campos,
                        eixo=None,
                        competency_ids=competency_ids,
                    )
                )
            link_neighbors(topics)
            label = source_id
            if kind == "competencia-especifica":
                competency = competencies[source_id]
                label = f"Competência específica {competency['numero']}"
                official_text = competency["texto"]
            elif kind == "campo-de-atuacao":
                label = contexts[source_id]
            units.append(
                {
                    "id": f"{subject_id}-{slugify(source_id)}",
                    "sourceId": source_id,
                    "name": label,
                    "kind": kind,
                    "official": True,
                    "sequenceKind": "document-order-adopted-as-naescola-proposal",
                    "officialText": official_text,
                    "topics": topics,
                }
            )
        add_subject(
            {
                "id": subject_id,
                "slug": slugify(name),
                "name": name,
                "componentId": component_id,
                "codeSigla": sigla,
                "areaId": area_id,
                "areaName": areas.get(area_id, area_id),
                "description": description,
                "officialStatus": official_status,
                "localDependencyNote": local_note,
                "units": finish_units(units),
            }
        )

    lp_groups: dict[tuple[str, str, str | None], list[dict]] = defaultdict(list)
    lgg_groups: dict[tuple[str, str, str | None], list[dict]] = defaultdict(list)
    area_groups: dict[str, dict[tuple[str, str, str | None], list[dict]]] = {
        "em-area-mat": defaultdict(list),
        "em-area-cnt": defaultdict(list),
        "em-area-chs": defaultdict(list),
    }
    for skill in medio["habilidades"]:
        if skill.get("seriacao") is not None:
            raise SystemExit(f"{skill['codigo']} has an unexpected série assignment.")
        if skill["codigo"].startswith("EM13LP"):
            campo = (skill.get("campos_atuacao_social") or [None])[0]
            if not campo:
                raise SystemExit(f"{skill['codigo']} has no campo de atuação.")
            lp_groups[("campo-de-atuacao", campo, None)].append(skill)
        elif skill["codigo"].startswith("EM13LGG"):
            competency_id = skill["competencias_especificas"][0]
            lgg_groups[("competencia-especifica", competency_id, None)].append(skill)
        elif skill["area"] in area_groups:
            competency_id = skill["competencias_especificas"][0]
            area_groups[skill["area"]][("competencia-especifica", competency_id, None)].append(skill)
        else:
            raise SystemExit(f"Unclassified Ensino Médio skill {skill['codigo']}")

    grouped_subject(
        subject_id="em-etapa-lp",
        name="Língua Portuguesa",
        sigla="LP",
        component_id="em-comp-lp",
        area_id="em-area-lgg",
        description="Habilidades oficiais de Língua Portuguesa no Ensino Médio, agrupadas pelos campos de atuação da fonte.",
        official_status="bncc-2018",
        local_note="A Lei nº 13.415/2017 determina a oferta de Língua Portuguesa nos três anos. A BNCC, ainda assim, não indica a série de cada habilidade.",
        groups=lp_groups,
    )
    grouped_subject(
        subject_id="em-etapa-lgg",
        name="Linguagens e suas Tecnologias",
        sigla="LGG",
        component_id="em-area-lgg",
        area_id="em-area-lgg",
        description="Habilidades da área. Arte, Educação Física e Língua Inglesa não têm códigos próprios neste documento.",
        official_status="bncc-2018",
        local_note="Os itinerários formativos também mobilizam estas competências e são definidos localmente. Não há lista nacional de itinerários neste arquivo.",
        groups=lgg_groups,
    )
    grouped_subject(
        subject_id="em-etapa-ma",
        name="Matemática",
        sigla="MA",
        component_id="em-comp-mat",
        area_id="em-area-mat",
        description="Habilidades da área Matemática e suas Tecnologias. Na BNCC, o detalhamento do componente coincide com a área.",
        official_status="bncc-2018",
        local_note="A Lei nº 13.415/2017 determina a oferta de Matemática nos três anos. A BNCC não reparte estas habilidades por série.",
        groups=area_groups["em-area-mat"],
    )
    grouped_subject(
        subject_id="em-etapa-cnt",
        name="Ciências da Natureza e suas Tecnologias",
        sigla="CNT",
        component_id="em-area-cnt",
        area_id="em-area-cnt",
        description="Habilidades da área. Biologia, Física e Química não têm códigos separados na BNCC do Ensino Médio.",
        official_status="bncc-2018",
        local_note=None,
        groups=area_groups["em-area-cnt"],
    )
    grouped_subject(
        subject_id="em-etapa-chs",
        name="Ciências Humanas e Sociais Aplicadas",
        sigla="CHS",
        component_id="em-area-chs",
        area_id="em-area-chs",
        description="Habilidades da área. História, Geografia, Sociologia e Filosofia não têm códigos separados na BNCC do Ensino Médio.",
        official_status="bncc-2018",
        local_note=None,
        groups=area_groups["em-area-chs"],
    )
    computing_groups: dict[tuple[str, str, str | None], list[dict]] = defaultdict(list)
    for skill in computing["habilidades_em"]:
        computing_groups[("competencia-especifica", skill["competencia"], None)].append(skill)
    grouped_subject(
        subject_id="em-etapa-co",
        name="Computação",
        sigla="CO",
        component_id="complemento-computacao",
        area_id="complemento-computacao-2022",
        description="Complemento de Computação do Parecer CNE/CEB nº 2/2022. Não faz parte do texto homologado da BNCC de 2018 e também não tem série.",
        official_status="complemento-computacao-2022",
        local_note="Complemento de 2022, não uma habilidade da BNCC de 2018.",
        groups=computing_groups,
    )
    area_names = areas
    for component_id, sigla, name, area_id, catalog_subject in EMPTY_COMPONENTS:
        add_subject(
            {
                "id": f"em-etapa-{sigla.lower()}",
                "slug": slugify(name),
                "name": name,
                "componentId": component_id,
                "codeSigla": sigla,
                "areaId": area_id,
                "areaName": area_names[area_id],
                "description": (
                    f"A BNCC nomeia {name} entre os componentes do Ensino Médio e não publica habilidades com código próprio. "
                    f"As habilidades oficiais estão em {catalog_subject}."
                ),
                "officialStatus": "bncc-2018",
                "localDependencyNote": (
                    "Componente sem habilidades próprias na BNCC de 2018. "
                    "A organização em disciplinas e itinerários depende do currículo local."
                ),
                "units": [],
            }
        )
    return {
        "schemaVersion": "1.0.0",
        "gradeId": "em-etapa",
        "gradeNumber": 0,
        "gradeLabel": "Etapa inteira",
        "stageId": "ensino-medio",
        "stageLabel": "Ensino Médio",
        "nomenclatureNote": (
            "A BNCC apresenta as habilidades do Ensino Médio sem indicação de seriação. "
            "Este arquivo não é a 1ª, a 2ª ou a 3ª série."
        ),
        "segmentKind": "etapa-sem-seriacao",
        "skillPlacement": "stage-not-a-year",
        "officialSkillCatalogId": None,
        "subjects": subjects,
        "omissions": [
            {
                "component": "Seriação nacional das habilidades",
                "reason": "No PDF da BNCC, página 34, as habilidades de Língua Portuguesa e Matemática são apresentadas sem indicação de seriação. O mesmo recorte do dataset marca seriacao nula em todas as habilidades do Ensino Médio.",
            },
            {
                "component": "Itinerários formativos",
                "reason": "A BNCC diz que as competências de área também se desenvolvem nos itinerários. A lista de itinerários não é nacional e não foi inventada aqui.",
            },
            {
                "component": "Ensino Religioso",
                "reason": "Não há componente de Ensino Religioso na BNCC do Ensino Médio. A Constituição, art. 210, §1º, situa o ensino religioso no ensino fundamental.",
            },
        ],
        "sources": stage_sources(base_sources),
        "notes": [
            "As habilidades e as competências específicas são oficiais. A ordem dentro de cada grupo é uma proposta da NaEscola.",
            "Lei nº 13.415/2017: Língua Portuguesa e Matemática devem ser oferecidas nos três anos. Isso não atribui cada código a uma série.",
            "Lei nº 14.945/2024 altera a organização do Ensino Médio. Este arquivo não converte essa lei em carga horária nem em habilidades novas.",
            "Não há pré-requisito afirmado entre o 9º ano e estas habilidades. A BNCC não publica esse vínculo.",
        ],
        "uncertainties": uncertainties()
        + [
            "Não foi conferido, habilidade por habilidade, o texto integral das 183 habilidades contra o PDF. A conferência pontual de EM13CHS101 bateu com a página PDF 574.",
            "A forma como cada rede distribui estas habilidades entre as três séries não está neste repositório.",
        ],
    }


def build_series(base_sources: list[dict], structure: dict) -> list[dict]:
    areas = {item["id"]: item["nome"] for item in structure["areas_conhecimento"]}
    documents = []
    ordinal = {1: "1ª", 2: "2ª", 3: "3ª"}
    for number in (1, 2, 3):
        subjects = []
        named = [
            ("em-comp-lp", "LP", "Língua Portuguesa", "em-area-lgg", True),
            ("em-area-lgg", "LGG", "Linguagens e suas Tecnologias", "em-area-lgg", True),
            ("em-comp-mat", "MA", "Matemática", "em-area-mat", True),
            ("em-area-cnt", "CNT", "Ciências da Natureza e suas Tecnologias", "em-area-cnt", True),
            ("em-area-chs", "CHS", "Ciências Humanas e Sociais Aplicadas", "em-area-chs", True),
            ("complemento-computacao", "CO", "Computação", "complemento-computacao-2022", False),
        ]
        for component_id, sigla, name, area_id, bncc in named:
            subjects.append(empty_series_subject(number, component_id, sigla, name, area_id, areas, bncc))
        for component_id, sigla, name, area_id, _catalog in EMPTY_COMPONENTS:
            subjects.append(empty_series_subject(number, component_id, sigla, name, area_id, areas, True))
        documents.append(
            {
                "schemaVersion": "1.0.0",
                "gradeId": f"em-{number}",
                "gradeNumber": number,
                "gradeLabel": f"{ordinal[number]} série",
                "stageId": "ensino-medio",
                "stageLabel": "Ensino Médio",
                "nomenclatureNote": (
                    f"A {ordinal[number]} série existe na organização escolar do Ensino Médio. "
                    "A BNCC não atribui habilidades a esta série. As habilidades oficiais estão na etapa inteira."
                ),
                "segmentKind": "serie",
                "skillPlacement": "series-has-no-official-skills",
                "officialSkillCatalogId": "em-etapa",
                "subjects": subjects,
                "omissions": [
                    {
                        "component": "Lista oficial de habilidades desta série",
                        "reason": "A BNCC declara que as habilidades do Ensino Médio são apresentadas sem indicação de seriação. A NaEscola não cria essa lista.",
                    },
                    {
                        "component": "Itinerários formativos",
                        "reason": "Dependem do sistema de ensino e da escola. A Lei nº 14.945/2024 muda a organização do Ensino Médio; o texto da lei não foi aberto neste ambiente.",
                    },
                ],
                "sources": stage_sources(base_sources),
                "notes": [
                    "Nenhum código BNCC foi colocado nesta série.",
                    "Língua Portuguesa e Matemática continuam obrigatórias nos três anos pela Lei nº 13.415/2017, sem que cada habilidade ganhe uma série.",
                ],
                "uncertainties": uncertainties(),
            }
        )
    return documents


def empty_series_subject(number: int, component_id: str, sigla: str, name: str, area_id: str, areas: dict[str, str], bncc: bool) -> dict:
    return {
        "id": f"em-{number}-{sigla.lower()}",
        "slug": slugify(name),
        "name": name,
        "componentId": component_id,
        "codeSigla": sigla,
        "areaId": area_id,
        "areaName": "Computação (complemento de 2022)" if area_id == "complemento-computacao-2022" else areas[area_id],
        "description": "As habilidades oficiais deste componente ou área estão no registro da etapa inteira, não nesta série.",
        "officialStatus": "bncc-2018" if bncc else "complemento-computacao-2022",
        "localDependencyNote": "A progressão por série é decisão do currículo local. Este cartão não contém uma lista oficial de habilidades da série.",
        "units": [],
    }


def competency_additions(structure: dict, computing: dict) -> dict:
    specific_medio = []
    for item in structure["competencias_especificas"]:
        area = item.get("area") or ""
        component = item.get("componente") or ""
        if not (area.startswith("em-") or component.startswith("em-")):
            continue
        specific_medio.append(
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
    computing_competencies = []
    for item in computing["competencias"]:
        computing_competencies.append(
            {
                "id": item["id"],
                "number": item["numero"],
                "text": item["texto"],
                "kind": item["tipo"],
                "areaId": None,
                "componentId": "complemento-computacao",
                "sourceLocator": item["fonte"].get("localizador"),
                "pdfLocator": item["fonte"].get("localizador_pdf"),
                "origin": "computacao-2022",
            }
        )
    rights = [
        {
            "id": right_id,
            "name": name,
            "text": text,
            "origin": "bncc-2018-pdf-page-40",
            "transcriptionNote": "Transcrição da página PDF 40, com hífens de quebra de linha recompostos. Não é um código de habilidade e não tem ordem de aula.",
        }
        for right_id, name, text in RIGHTS
    ]
    return {
        "specificMedio": specific_medio,
        "earlyChildhoodRights": rights,
        "computingCompetencies": computing_competencies,
    }
