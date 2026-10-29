"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Remote } from "@/components/Remote";

type Grade = {
  id: string;
  label: string;
  subjects: Array<{ name: string }>;
  publishedLessonCount: number;
  coveragePercent: number;
};

function formatPercent(value: number) {
  return `${value.toLocaleString("pt-BR")}% dos tópicos`;
}

export default function StagePage() {
  const params = useParams<{ stageId: string }>();
  return (
    <Remote<{ label: string; grades: Grade[] }> path={`/api/stages/${params.stageId}`}>
      {(stage) => (
        <>
          <h1>{stage.label}</h1>
          {stage.grades.length === 0 ? <p>Não há anos carregados nesta etapa.</p> : (
            <div className="grid cards">
              {stage.grades.map((grade) => (
                <Link key={grade.id} className="card" href={`/anos/${grade.id}`}>
                  <h2>{grade.label}</h2>
                  {grade.subjects.length > 0 ? <p>{grade.subjects.map((subject) => subject.name).join(", ")}</p> : null}
                  <div className="meta">
                    <span className="pill">{grade.publishedLessonCount} aulas</span>
                    <span className="pill">{formatPercent(grade.coveragePercent)}</span>
                  </div>
                  <div className="meter" aria-hidden="true"><span style={{ width: `${Math.min(grade.coveragePercent, 100)}%` }} /></div>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </Remote>
  );
}
