"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type RefObject } from "react";

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
type Subject = {
  id: string;
  name: string;
  description: string;
  officialStatus: string;
  localDependencyNote: string | null;
  units: Unit[];
  topicCount: number;
  publishedLessonCount: number;
  coveragePercent: number;
};
type ListedTopic = Topic & { unitId: string; unitName: string };

const KIND_LABEL: Record<string, string> = {
  conceptual: "Dependência conceitual proposta pela NaEscola",
  "cross-subject": "Ligação proposta entre componentes",
  "same-official-code-previous-year": "Mesmo código oficial no ano anterior",
};

function formatPercent(published: number, total: number) {
  const value = total ? Math.round((1000 * published) / total) / 10 : 0;
  return value.toLocaleString("pt-BR");
}

export function Timeline({ gradeId, subject, initialTopicId }: { gradeId: string; subject: Subject; initialTopicId?: string }) {
  const [open, setOpen] = useState<string[]>(subject.units.slice(0, 1).map((unit) => unit.id));
  const [selectedId, setSelectedId] = useState<string | null>(initialTopicId ?? null);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const closeRef = useRef<HTMLButtonElement>(null);
  const topics = useMemo(
    () => subject.units.flatMap((unit) => unit.topics.map((topic) => ({ ...topic, unitId: unit.id, unitName: unit.name }))),
    [subject],
  );
  const selected = topics.find((topic) => topic.id === selectedId) ?? null;
  const prerequisiteIds = new Set(selected?.prerequisites.map((item) => item.topicId) ?? []);

  useEffect(() => {
    if (!selected) return;
    setOpen((current) => (current.includes(selected.unitId) ? current : [...current, selected.unitId]));
    closeRef.current?.focus();
  }, [selected]);

  useEffect(() => {
    if (!selected) return undefined;
    function onKey(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") setSelectedId(null);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
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
    const next = event.key === "ArrowDown" ? shown[Math.max(index, 0) + (index < 0 ? 0 : 1)] : shown[index - 1];
    if (!next) return;
    event.preventDefault();
    setSelectedId(next.id);
  }

  return (
    <div>
      <p className="coverage-line">
        {subject.publishedLessonCount} de {subject.topicCount} tópicos com aula publicada ({subject.coveragePercent.toLocaleString("pt-BR")}%).
      </p>
      {subject.officialStatus === "complemento-computacao-2022" ? <p>Computação é o complemento de 2022, não uma habilidade da BNCC de 2018.</p> : null}
      {subject.localDependencyNote ? <p>{subject.localDependencyNote}</p> : null}
      <div className="toolbar-stretch">
        <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Filtrar tópicos" placeholder="Filtrar por nome ou código" />
        <select aria-label="Situação" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="all">Todos</option>
          <option value="published">Com aula publicada</option>
          <option value="planned">Ainda sem aula</option>
        </select>
      </div>
      <div onKeyDown={onKey}>
        {subject.units.map((unit) => {
          const shown = unit.topics.filter(visible);
          if (shown.length === 0) return null;
          const published = unit.topics.filter((topic) => topic.coverageStatus === "published").length;
          const expanded = open.includes(unit.id);
          return (
            <section key={unit.id} className="cluster">
              <header>
                <h3>
                  <button type="button" className="secondary" aria-expanded={expanded} onClick={() => setOpen((current) => expanded ? current.filter((id) => id !== unit.id) : [...current, unit.id])}>
                    {unit.name}
                  </button>
                </h3>
                <p>{published} de {unit.topics.length} com aula ({formatPercent(published, unit.topics.length)}%)</p>
              </header>
              {expanded ? (
                <ol className="topic-list">
                  {shown.map((topic) => {
                    const ready = topic.coverageStatus === "published";
                    return (
                      <li key={topic.id}>
                        <button
                          type="button"
                          className={`topic-row${ready ? " is-published" : " is-planned"}${prerequisiteIds.has(topic.id) ? " is-prerequisite" : ""}`}
                          aria-current={selectedId === topic.id}
                          aria-haspopup="dialog"
                          onClick={() => setSelectedId(topic.id)}
                        >
                          <span className={ready ? "badge badge-published" : "badge badge-planned"}>{ready ? "Com aula" : "Sem aula"}</span>
                          <span className="topic-name">{topic.proposedOrder}. {topic.bnccSkillCodes[0]} — {topic.name}</span>
                        </button>
                      </li>
                    );
                  })}
                </ol>
              ) : null}
            </section>
          );
        })}
      </div>
      {selected ? <TopicDialog topic={selected} topics={topics} onSelect={setSelectedId} onClose={() => setSelectedId(null)} closeRef={closeRef} /> : null}
      <p><Link href={`/anos/${gradeId}`}>Voltar ao ano</Link></p>
    </div>
  );
}

function TopicDialog({
  topic,
  topics,
  onSelect,
  onClose,
  closeRef,
}: {
  topic: ListedTopic;
  topics: ListedTopic[];
  onSelect: (id: string) => void;
  onClose: () => void;
  closeRef: RefObject<HTMLButtonElement | null>;
}) {
  const ready = topic.coverageStatus === "published";
  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="topic-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-bar">
          <span className={ready ? "badge badge-published" : "badge badge-planned"}>{ready ? "Com aula" : "Sem aula"}</span>
          <button ref={closeRef} type="button" className="secondary" onClick={onClose}>Fechar</button>
        </div>
        <p className="crumb">{topic.unitName}</p>
        <h3 id="topic-dialog-title">{topic.name}</h3>
        <p>{topic.summary}</p>
        <p>{topic.sequenceBasis}</p>
        {topic.flags.length > 0 ? <p>Sinais: {topic.flags.join(", ")}.</p> : null}
        <h4>Pré-requisitos</h4>
        {topic.prerequisites.length === 0 ? <p>Nenhum pré-requisito proposto.</p> : (
          <ul>
            {topic.prerequisites.map((item) => {
              const target = topics.find((candidate) => candidate.id === item.topicId);
              return (
                <li key={item.topicId}>
                  {target ? <button type="button" className="secondary" onClick={() => onSelect(item.topicId)}>{target.bnccSkillCodes[0]}</button> : item.topicId}
                  {" "}{KIND_LABEL[item.kind] ?? item.kind}. {item.note}
                </li>
              );
            })}
          </ul>
        )}
        {topic.publishedLessonSlugs[0] ? <Link className="button" href={`/aulas/${topic.publishedLessonSlugs[0]}`}>Abrir aula</Link> : <p>Ainda não há aula publicada para este tópico.</p>}
      </div>
    </div>
  );
}
