"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, type KeyboardEvent } from "react";

type Prerequisite = { topicId: string; kind: string; note: string };
type Topic = {
  id: string;
  name: string;
  summary: string;
  bnccSkillCodes: string[];
  proposedOrder: number;
  sequenceBasis: string;
  coverageStatus: string;
  publishedLessonSlugs: string[];
  prerequisites: Prerequisite[];
  flags: string[];
};
type Unit = { id: string; name: string; kind: string; topics: Topic[] };
type Subject = { id: string; name: string; description: string; officialStatus: string; localDependencyNote: string | null; units: Unit[]; topicCount: number; publishedLessonCount: number; coveragePercent: number };

const KIND_LABEL: Record<string, string> = {
  conceptual: "Dependência conceitual proposta pela NaEscola",
  "cross-subject": "Ligação proposta entre componentes",
  "same-official-code-previous-year": "Mesmo código oficial no ano anterior",
};

export function Timeline({ gradeId, subject, sequenceNote, initialTopicId }: { gradeId: string; subject: Subject; sequenceNote: string; initialTopicId?: string }) {
  const [open, setOpen] = useState<string[]>(subject.units.slice(0, 1).map((unit) => unit.id));
  const [selectedId, setSelectedId] = useState<string | null>(initialTopicId ?? null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [mode, setMode] = useState<"timeline" | "list">("timeline");
  const topics = useMemo(() => subject.units.flatMap((unit) => unit.topics.map((topic) => ({ ...topic, unitId: unit.id, unitName: unit.name }))), [subject]);
  const selected = topics.find((topic) => topic.id === selectedId) ?? null;
  const prerequisiteIds = new Set(selected?.prerequisites.map((item) => item.topicId) ?? []);

  useEffect(() => {
    if (!selected) return;
    setOpen((current) => current.includes(selected.unitId) ? current : [...current, selected.unitId]);
  }, [selected]);

  function visible(topic: Topic) {
    const haystack = `${topic.name} ${topic.bnccSkillCodes.join(" ")} ${topic.summary}`.toLocaleLowerCase("pt-BR");
    if (query && !haystack.includes(query.toLocaleLowerCase("pt-BR"))) return false;
    if (status === "published") return topic.coverageStatus === "published";
    if (status === "planned") return topic.coverageStatus !== "published";
    return true;
  }

  function onKey(event: KeyboardEvent) {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
    const shown = topics.filter(visible);
    const index = shown.findIndex((topic) => topic.id === selectedId);
    const next = event.key === "ArrowDown" ? shown[index + 1] : shown[index - 1];
    if (!next) return;
    event.preventDefault();
    setSelectedId(next.id);
  }

  return (
    <div>
      <p>{sequenceNote}</p>
      <p>{subject.publishedLessonCount} de {subject.topicCount} tópicos com aula publicada ({subject.coveragePercent}%).</p>
      {subject.officialStatus === "complemento-computacao-2022" ? <p>Computação é o complemento de 2022, não uma habilidade da BNCC de 2018.</p> : null}
      {subject.localDependencyNote ? <p>{subject.localDependencyNote}</p> : null}
      <div className="toolbar">
        <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Filtrar tópicos" placeholder="Filtrar por nome ou código" />
        <select aria-label="Situação" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="all">Todos</option>
          <option value="published">Com aula publicada</option>
          <option value="planned">Ainda sem aula</option>
        </select>
        <button type="button" className="secondary" aria-pressed={mode === "timeline"} onClick={() => setMode("timeline")}>Linha do tempo</button>
        <button type="button" className="secondary" aria-pressed={mode === "list"} onClick={() => setMode("list")}>Lista</button>
      </div>
      <div className="timeline-layout">
        <div onKeyDown={onKey}>
          {subject.units.map((unit) => {
            const shown = unit.topics.filter(visible);
            if (shown.length === 0) return null;
            const expanded = open.includes(unit.id);
            return (
              <section key={unit.id} className={mode === "timeline" ? "unit" : undefined}>
                <h3>
                  <button type="button" className="secondary" aria-expanded={expanded} onClick={() => setOpen((current) => expanded ? current.filter((id) => id !== unit.id) : [...current, unit.id])}>
                    {unit.name}
                  </button>
                </h3>
                {expanded ? (
                  <ol>
                    {shown.map((topic) => (
                      <li key={topic.id}>
                        <button
                          type="button"
                          className={`topic-button${prerequisiteIds.has(topic.id) ? " is-prerequisite" : ""}`}
                          aria-current={selectedId === topic.id}
                          onClick={() => setSelectedId(topic.id)}
                        >
                          <span className={topic.coverageStatus === "published" ? "status-published" : "status-planned"}>
                            {topic.coverageStatus === "published" ? "Publicada" : "Planejada"}
                          </span>
                          {" "}{topic.proposedOrder}. {topic.bnccSkillCodes[0]} — {topic.name}
                        </button>
                      </li>
                    ))}
                  </ol>
                ) : <p>{shown.length} tópicos ocultos.</p>}
              </section>
            );
          })}
        </div>
        <aside className="panel" aria-live="polite">
          {selected ? (
            <>
              <h3>{selected.name}</h3>
              <p>{selected.summary}</p>
              <p>{selected.sequenceBasis}</p>
              {selected.flags.length > 0 ? <p>Sinais: {selected.flags.join(", ")}.</p> : null}
              <h4>Pré-requisitos</h4>
              {selected.prerequisites.length === 0 ? <p>Nenhum pré-requisito proposto.</p> : (
                <ul>
                  {selected.prerequisites.map((item) => {
                    const target = topics.find((topic) => topic.id === item.topicId);
                    return (
                      <li key={item.topicId}>
                        {target ? <button type="button" className="secondary" onClick={() => setSelectedId(item.topicId)}>{target.bnccSkillCodes[0]}</button> : item.topicId}
                        {" "}{KIND_LABEL[item.kind] ?? item.kind}. {item.note}
                      </li>
                    );
                  })}
                </ul>
              )}
              {selected.publishedLessonSlugs[0] ? <Link className="button" href={`/aulas/${selected.publishedLessonSlugs[0]}`}>Abrir aula</Link> : <p>Ainda não há aula publicada para este tópico.</p>}
            </>
          ) : <p>Escolha um tópico para ver a habilidade oficial, a ordem proposta e os pré-requisitos.</p>}
        </aside>
      </div>
      <p><Link href={`/anos/${gradeId}`}>Voltar ao ano</Link></p>
    </div>
  );
}
