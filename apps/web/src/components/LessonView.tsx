"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrayGrid, BarCompare, FunctionPlot, NumberLine } from "./viz/Charts";
import { Comparison, EventTimeline, FieldRecord, GeometryDiagram, StateSteps } from "./viz/Diagrams";
import { TerritoryMap } from "./viz/TerritoryMap";

type Block = { type: string; [key: string]: unknown };

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

function KnowledgeCheck({ block }: { block: Block }) {
  const choices = block.choices as Array<{ id: string; text: string }>;
  const [picked, setPicked] = useState<string | null>(null);
  const correct = picked === block.correctChoiceId;
  return (
    <fieldset className="lesson-block">
      <legend>{String(block.prompt)}</legend>
      {choices.map((choice) => (
        <button key={choice.id} type="button" className="choice" aria-pressed={picked === choice.id} onClick={() => setPicked(choice.id)}>
          {choice.text}
        </button>
      ))}
      <p className="feedback" aria-live="polite">
        {picked === null ? "" : correct ? String(block.feedbackCorrect) : String(block.feedbackIncorrect)}
      </p>
    </fieldset>
  );
}

export function LessonView({ payload }: { payload: Record<string, unknown> }) {
  const lesson = payload.lesson as Record<string, unknown>;
  const placement = payload.placement as Record<string, string | number>;
  const prerequisites = payload.prerequisites as Array<Record<string, string | null>>;
  const neighbors = payload.neighbors as { previous: Record<string, string | null> | null; next: Record<string, string | null> | null };
  const blocks = lesson.blocks as Block[];
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
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          const Tag = block.level === 3 ? "h3" : "h2";
          return <Tag key={index}>{String(block.text)}</Tag>;
        }
        if (block.type === "paragraph") return <p key={index}>{String(block.text)}</p>;
        if (block.type === "callout") {
          return <aside key={index} className={`callout ${String(block.tone)}`}><h2>{String(block.title)}</h2><p>{String(block.text)}</p></aside>;
        }
        if (block.type === "worked-example") {
          return (
            <section key={index} className="panel">
              <h2>{String(block.title)}</h2>
              <p>{String(block.prompt)}</p>
              <ol>{(block.steps as string[]).map((step) => <li key={step}>{step}</li>)}</ol>
              <p>{String(block.conclusion)}</p>
            </section>
          );
        }
        if (block.type === "visualization") {
          return (
            <section key={index} className="lesson-block">
              <h2>{String(block.title)}</h2>
              <Visualization block={block} />
            </section>
          );
        }
        if (block.type === "knowledge-check") return <KnowledgeCheck key={index} block={block} />;
        if (block.type === "summary") {
          return <section key={index}><h2>Para lembrar</h2><ul>{(block.points as string[]).map((point) => <li key={point}>{point}</li>)}</ul></section>;
        }
        return null;
      })}
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
