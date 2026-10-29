"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { Remote } from "@/components/Remote";

type Stage = {
  id: string;
  label: string;
  coveragePercent: number;
  publishedLessonCount: number;
  topicCount: number;
};

type SearchHit = {
  topics: Array<{ topicId: string; name: string; gradeId: string; gradeLabel: string; subjectId: string; subjectName: string; bnccSkillCodes: string[] }>;
  lessons: Array<{ slug: string; title: string }>;
};

function formatPercent(value: number) {
  return `${value.toLocaleString("pt-BR")}% dos tópicos`;
}

function HomeBody() {
  const params = useSearchParams();
  const initial = params.get("q") ?? "";
  const [query, setQuery] = useState(initial);
  const [submitted, setSubmitted] = useState(initial.trim());

  function submit(event: FormEvent) {
    event.preventDefault();
    const next = query.trim();
    setSubmitted(next);
    const url = next ? `/?q=${encodeURIComponent(next)}` : "/";
    window.history.replaceState(null, "", url);
  }

  return (
    <>
      <div className="home-search">
        <h1>Buscar Conhecimento</h1>
        <form className="search" onSubmit={submit}>
          <label htmlFor="q">Buscar habilidade ou aula</label>
          <input id="q" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Habilidade, código ou aula" />
          <button type="submit">Buscar</button>
        </form>
      </div>
      {submitted.length >= 2 ? (
        <Remote<SearchHit> path={`/api/search?q=${encodeURIComponent(submitted)}`}>
          {(data) => (
            <section className="search-results">
              <h2>Tópicos</h2>
              {data.topics.length === 0 ? <p>Nenhum tópico com esse termo.</p> : (
                <ul>
                  {data.topics.map((topic) => (
                    <li key={topic.topicId}>
                      <Link href={`/anos/${topic.gradeId}/${topic.subjectId}?topico=${topic.topicId}`}>{topic.bnccSkillCodes[0]} — {topic.name}</Link>
                      {" "}({topic.gradeLabel}, {topic.subjectName})
                    </li>
                  ))}
                </ul>
              )}
              <h2>Aulas publicadas</h2>
              {data.lessons.length === 0 ? <p>Nenhuma aula publicada com esse termo.</p> : (
                <ul>{data.lessons.map((lesson) => <li key={lesson.slug}><Link href={`/aulas/${lesson.slug}`}>{lesson.title}</Link></li>)}</ul>
              )}
            </section>
          )}
        </Remote>
      ) : submitted.length > 0 ? <p>Digite pelo menos duas letras.</p> : null}
      <Remote<{ stages: Stage[] }> path="/api/stages">
        {(data) => (
          <div className="grid stages">
            {data.stages.map((stage) => (
              <Link key={stage.id} className={`card stage-${stage.id}`} href={`/etapas/${stage.id}`}>
                <h2>{stage.label}</h2>
                <div className="meta">
                  <span className="pill">{formatPercent(stage.coveragePercent)}</span>
                  <span className="pill">{stage.publishedLessonCount} aulas publicadas</span>
                </div>
                <div className="meter" aria-hidden="true"><span style={{ width: `${Math.min(stage.coveragePercent, 100)}%` }} /></div>
              </Link>
            ))}
          </div>
        )}
      </Remote>
    </>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<p role="status">Carregando…</p>}>
      <HomeBody />
    </Suspense>
  );
}
