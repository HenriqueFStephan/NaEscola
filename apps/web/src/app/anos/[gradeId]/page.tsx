"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Remote } from "@/components/Remote";

type Subject = { id: string; name: string; description: string; officialStatus: string; topicCount: number; publishedLessonCount: number; coveragePercent: number };
type Grade = { label: string; description: string; status: string; subjects: Subject[]; omissions: Array<{ component: string; reason: string }>; publishedLessonCount: number; coveragePercent: number };

export default function GradePage() {
  const params = useParams<{ gradeId: string }>();
  return (
    <Remote<Grade> path={`/api/grades/${params.gradeId}`}>
      {(grade) => (
        <>
          <h1>{grade.label}</h1>
          <p>{grade.description}</p>
          <p>{grade.publishedLessonCount} aulas publicadas. Cobertura dos tópicos carregados: {grade.coveragePercent}%.</p>
          {grade.status !== "curriculum_loaded" ? <p>Este ano está na estrutura da educação básica, mas o currículo ainda não foi montado.</p> : null}
          {grade.omissions.map((item) => <p key={item.component}><strong>{item.component}.</strong> {item.reason}</p>)}
          <div className="grid cards">
            {grade.subjects.map((subject) => (
              <Link key={subject.id} className="card" href={`/anos/${params.gradeId}/${subject.id}`}>
                <h2>{subject.name}</h2>
                <p>{subject.description}</p>
                <div className="meta">
                  <span className="pill">{subject.officialStatus === "bncc-2018" ? "BNCC 2018" : "Complemento 2022"}</span>
                  <span className="pill">{subject.topicCount} habilidades</span>
                  <span className="pill">{subject.publishedLessonCount} aulas</span>
                  <span className="pill">{subject.coveragePercent}%</span>
                </div>
                <div className="meter" aria-hidden="true"><span style={{ width: `${subject.coveragePercent}%` }} /></div>
              </Link>
            ))}
          </div>
        </>
      )}
    </Remote>
  );
}
