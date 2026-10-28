"use client";

import { Remote } from "@/components/Remote";

type Competency = { id: string; number: number; text: string; kind?: string; componentId?: string | null; areaId?: string | null };

export default function CompetenciesPage() {
  return (
    <Remote<{ note: string; general: Competency[]; specificFundamental: Competency[] }> path="/api/competencies">
      {(data) => (
        <>
          <h1>Competências oficiais</h1>
          <p>{data.note}</p>
          <h2>Gerais</h2>
          <ol>{data.general.map((item) => <li key={item.id}>{item.text}</li>)}</ol>
          <h2>Específicas do Ensino Fundamental</h2>
          <ul>{data.specificFundamental.map((item) => <li key={item.id}>{item.text}</li>)}</ul>
        </>
      )}
    </Remote>
  );
}
