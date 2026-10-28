"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Remote } from "@/components/Remote";

type Grade = { id: string; label: string; status: string; description: string; subjects: Array<{ name: string }>; publishedLessonCount: number; coveragePercent: number };

export default function StagePage() {
  const params = useParams<{ stageId: string }>();
  return (
    <Remote<{ label: string; summary: string; grades: Grade[] }> path={`/api/stages/${params.stageId}`}>
      {(stage) => (
        <>
          <h1>{stage.label}</h1>
          <p>{stage.summary}</p>
          {stage.grades.length === 0 ? <p>Não há anos carregados nesta etapa.</p> : (
            <div className="grid cards">
              {stage.grades.map((grade) => (
                <Link key={grade.id} className="card" href={`/anos/${grade.id}`}>
                  <h2>{grade.label}</h2>
                  <p>{grade.description}</p>
                  <p>{grade.subjects.length ? grade.subjects.map((subject) => subject.name).join(", ") : "Componentes ainda não pesquisados."}</p>
                  <div className="meta">
                    <span className="pill">{grade.publishedLessonCount} aulas</span>
                    <span className="pill">{grade.coveragePercent}% dos tópicos</span>
                  </div>
                  <div className="meter" aria-hidden="true"><span style={{ width: `${grade.coveragePercent}%` }} /></div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </Remote>
  );
}
