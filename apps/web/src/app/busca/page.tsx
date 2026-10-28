"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { Remote } from "@/components/Remote";

function SearchBody() {
  const params = useSearchParams();
  const initial = params.get("q") ?? "";
  const [query, setQuery] = useState(initial);
  const [submitted, setSubmitted] = useState(initial);
  function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitted(query.trim());
  }
  return (
    <>
      <h1>Busca</h1>
      <form className="search" onSubmit={submit}>
        <label htmlFor="busca">Termo</label>
        <input id="busca" type="search" value={query} onChange={(event) => setQuery(event.target.value)} />
        <button type="submit">Buscar</button>
      </form>
      {submitted.length >= 2 ? (
        <Remote<{ topics: Array<{ topicId: string; name: string; gradeId: string; gradeLabel: string; subjectId: string; subjectName: string; bnccSkillCodes: string[] }>; lessons: Array<{ slug: string; title: string }> }> path={`/api/search?q=${encodeURIComponent(submitted)}`}>
          {(data) => (
            <>
              <h2>Tópicos</h2>
              <ul>
                {data.topics.map((topic) => (
                  <li key={topic.topicId}>
                    <Link href={`/anos/${topic.gradeId}/${topic.subjectId}?topico=${topic.topicId}`}>{topic.bnccSkillCodes[0]} — {topic.name}</Link>
                    {" "}({topic.gradeLabel}, {topic.subjectName})
                  </li>
                ))}
              </ul>
              <h2>Aulas publicadas</h2>
              <ul>{data.lessons.map((lesson) => <li key={lesson.slug}><Link href={`/aulas/${lesson.slug}`}>{lesson.title}</Link></li>)}</ul>
            </>
          )}
        </Remote>
      ) : <p>Digite pelo menos duas letras.</p>}
    </>
  );
}

export default function SearchPage() {
  return <Suspense fallback={<p role="status">Carregando…</p>}><SearchBody /></Suspense>;
}
