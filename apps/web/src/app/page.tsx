"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Remote } from "@/components/Remote";

type Stage = { id: string; label: string; summary: string; status: string; grades: Array<{ publishedLessonCount: number }> };

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  function submit(event: FormEvent) {
    event.preventDefault();
    router.push(`/busca?q=${encodeURIComponent(query)}`);
  }
  return (
    <>
      <h1>Um caminho pelo conhecimento escolar</h1>
      <p className="lede">A NaEscola organiza etapas, anos e componentes. Nesta versão, o currículo carregado é o dos 3º, 4º, 5º e 6º anos. O que ainda não foi pesquisado aparece como planejado, sem números inventados.</p>
      <form className="search" onSubmit={submit}>
        <label htmlFor="q">Buscar habilidade ou aula</label>
        <input id="q" type="search" value={query} onChange={(event) => setQuery(event.target.value)} />
        <button type="submit">Buscar</button>
      </form>
      <Remote<{ stages: Stage[] }> path="/api/stages">
        {(data) => (
          <div className="grid stages">
            {data.stages.map((stage) => {
              const published = stage.grades.reduce((sum, grade) => sum + grade.publishedLessonCount, 0);
              return (
                <Link key={stage.id} className={`card stage-${stage.id}`} href={`/etapas/${stage.id}`}>
                  <h2>{stage.label}</h2>
                  <p>{stage.summary}</p>
                  <div className="meta">
                    <span className="pill">{stage.status === "not_researched" || stage.status === "planned_phase_2" ? "Planejada" : "Em construção"}</span>
                    <span className="pill">{published} aulas publicadas</span>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </Remote>
    </>
  );
}
