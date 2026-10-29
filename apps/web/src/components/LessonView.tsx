"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrayGrid, BarCompare, FunctionPlot, NumberLine } from "./viz/Charts";
import { Comparison, EventTimeline, FieldRecord, GeometryDiagram, StateSteps } from "./viz/Diagrams";
import { TerritoryMap } from "./viz/TerritoryMap";

type Block = { type: string; [key: string]: unknown };
type Choice = { id: string; text: string; explanation?: string };

function Visualization({ block }: { block: Block }) {
  const config = block.config as Record<string, unknown>;
  const description = String(block.description);
  const common = { config, description };
  switch (block.component) {
    case "function-plot": return <FunctionPlot {...common} />;
    case "number-line": return <NumberLine {...common} />;
    case "array-grid": return <ArrayGrid {...common} />;
    case "bar-compare": return <BarCompare {...common} />;
    case "geometry-diagram": return <GeometryDiagram {...common} />;
    case "comparison": return <Comparison {...common} />;
    case "event-timeline": return <EventTimeline {...common} />;
    case "state-steps": return <StateSteps {...common} />;
    case "field-record": return <FieldRecord {...common} />;
    case "territory-map": return <TerritoryMap {...common} />;
    default: return <p>Componente de visualização desconhecido.</p>;
  }
}

function KnowledgeCheck({ block, index, total }: { block: Block; index: number; total: number }) {
  const choices = block.choices as Choice[];
  const [picked, setPicked] = useState<string | null>(null);
  const correct = picked === block.correctChoiceId;
  const chosen = choices.find((choice) => choice.id === picked);
  return (
    <fieldset className={`lesson-block check${picked === null ? "" : correct ? " is-correct" : " is-incorrect"}`}>
      <legend>Pergunta {index} de {total}</legend>
      <p className="prompt">{String(block.prompt)}</p>
      {choices.map((choice) => (
        <button key={choice.id} type="button" className="choice" aria-pressed={picked === choice.id} onClick={() => setPicked(choice.id)}>
          {choice.text}
        </button>
      ))}
      {picked !== null ? (
        <div className="feedback" aria-live="polite">
          <p>{correct ? String(block.feedbackCorrect) : String(block.feedbackIncorrect)}</p>
          {chosen?.explanation ? <p>{chosen.explanation}</p> : null}
        </div>
      ) : null}
    </fieldset>
  );
}

function ReadingBlock({ block }: { block: Block }) {
  if (block.type === "heading") {
    const Tag = block.level === 3 ? "h3" : "h2";
    return <Tag>{String(block.text)}</Tag>;
  }
  if (block.type === "paragraph") return <p>{String(block.text)}</p>;
  if (block.type === "callout") {
    return <aside className={`callout ${String(block.tone)}`}><h2>{String(block.title)}</h2><p>{String(block.text)}</p></aside>;
  }
  if (block.type === "worked-example") {
    return (
      <section className="panel">
        <h2>{String(block.title)}</h2>
        <p>{String(block.prompt)}</p>
        <ol>{(block.steps as string[]).map((step) => <li key={step}>{step}</li>)}</ol>
        <p>{String(block.conclusion)}</p>
      </section>
    );
  }
  return null;
}

export function LessonView({ payload }: { payload: Record<string, unknown> }) {
  const lesson = payload.lesson as Record<string, unknown>;
  const placement = payload.placement as Record<string, string | number>;
  const prerequisites = payload.prerequisites as Array<Record<string, string | null>>;
  const neighbors = payload.neighbors as { previous: Record<string, string | null> | null; next: Record<string, string | null> | null };
  const blocks = lesson.blocks as Block[];
  const reading = blocks.filter((block) => ["heading", "paragraph", "callout", "worked-example"].includes(block.type));
  const visuals = blocks.filter((block) => block.type === "visualization");
  const checks = blocks.filter((block) => block.type === "knowledge-check");
  const summary = blocks.find((block) => block.type === "summary");
  const [tab, setTab] = useState(0);
  const active = visuals[tab] ?? visuals[0];

  return (
    <article>
      <p>{String(placement.gradeLabel)} · {String(placement.subjectName)} · {String(placement.unitName)}</p>
      <h1>{String(lesson.title)}</h1>
      <p>{String(lesson.sequenceNote)}</p>
      <p>Posição proposta na unidade: {String(placement.proposedOrder)}.</p>
      <h2>Objetivos</h2>
      <ul>{(lesson.learningObjectives as string[]).map((item) => <li key={item}>{item}</li>)}</ul>
      <p>Códigos oficiais: {(lesson.bnccSkillCodes as string[]).join(", ")}. O enunciado oficial não foi reescrito como se fosse uma sequência obrigatória de aulas.</p>
      {prerequisites.length > 0 ? (
        <>
          <h2>Pré-requisitos propostos</h2>
          <ul>
            {prerequisites.map((item) => (
              <li key={String(item.topicId)}>
                {item.lessonSlug ? <Link href={`/aulas/${item.lessonSlug}`}>{item.name}</Link> : String(item.name)}
                {" "}({item.gradeLabel}, {item.subjectName}). {item.note}
              </li>
            ))}
          </ul>
        </>
      ) : null}
      {reading.map((block, index) => <ReadingBlock key={index} block={block} />)}
      {active ? (
        <section className="lesson-block">
          <h2>Ferramentas</h2>
          <div className="tablist" role="tablist" aria-label="Modos de visualização">
            {visuals.map((block, index) => (
              <button
                key={String(block.title)}
                type="button"
                className="secondary"
                role="tab"
                id={`viz-tab-${index}`}
                aria-selected={index === tab}
                aria-controls={`viz-panel-${index}`}
                onClick={() => setTab(index)}
              >
                {String(block.title)}
              </button>
            ))}
          </div>
          <div role="tabpanel" id={`viz-panel-${tab}`} aria-labelledby={`viz-tab-${tab}`}>
            <h3>{String(active.title)}</h3>
            <Visualization block={active} />
          </div>
        </section>
      ) : null}
      {checks.length > 0 ? (
        <section className="test">
          <h2>Verificação</h2>
          <p>Responda cada pergunta. O retorno explica a escolha, certa ou errada.</p>
          {checks.map((block, index) => <KnowledgeCheck key={String(block.id)} block={block} index={index + 1} total={checks.length} />)}
        </section>
      ) : null}
      {summary ? (
        <section>
          <h2>Para lembrar</h2>
          <ul>{(summary.points as string[]).map((point) => <li key={point}>{point}</li>)}</ul>
        </section>
      ) : null}
      {(lesson.uncertaintyNotes as string[]).length > 0 ? (
        <section>
          <h2>Limites</h2>
          <ul>{(lesson.uncertaintyNotes as string[]).map((note) => <li key={note}>{note}</li>)}</ul>
        </section>
      ) : null}
      <section>
        <h2>Referências</h2>
        <ul>
          {(lesson.references as Array<Record<string, string | null>>).map((reference) => (
            <li key={String(reference.id)}>
              {reference.url ? <a href={String(reference.url)}>{reference.title}</a> : reference.title}
              . {reference.authorOrInstitution}. {reference.identifier ? `Identificador: ${reference.identifier}. ` : ""}
              Acesso em {reference.accessedAt}. {reference.reliabilityNote}
            </li>
          ))}
        </ul>
      </section>
      <nav className="toolbar" aria-label="Aulas vizinhas na sequência proposta">
        <Neighbor link={neighbors.previous} label="Anterior" />
        <Neighbor link={neighbors.next} label="Próxima" />
      </nav>
    </article>
  );
}

function Neighbor({ link, label }: { link: Record<string, string | null> | null; label: string }) {
  if (!link) return null;
  if (link.lessonSlug) return <Link className="button secondary" href={`/aulas/${link.lessonSlug}`}>{label}: {link.name}</Link>;
  return <span className="pill">{label} ainda sem aula publicada: {link.name}</span>;
}
