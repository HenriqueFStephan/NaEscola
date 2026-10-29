"use client";

import { Remote } from "@/components/Remote";

type Competency = { id: string; number?: number; name?: string; text: string; kind?: string; componentId?: string | null; areaId?: string | null; transcriptionNote?: string };
type Payload = {
  note: string;
  general: Competency[];
  specificFundamental: Competency[];
  specificMedio?: Competency[];
  earlyChildhoodRights?: Competency[];
  computingCompetencies?: Competency[];
};

export default function CompetenciesPage() {
  return (
    <Remote<Payload> path="/api/competencies">
      {(data) => (
        <>
          <h1>Competências oficiais</h1>
          <p>{data.note}</p>
          <h2>Gerais</h2>
          <ol>{data.general.map((item) => <li key={item.id}>{item.text}</li>)}</ol>
          <h2>Específicas do Ensino Fundamental</h2>
          <ul>{data.specificFundamental.map((item) => <li key={item.id}>{item.text}</li>)}</ul>
          <h2>Específicas do Ensino Médio</h2>
          <ul>{(data.specificMedio ?? []).map((item) => <li key={item.id}>{item.text}</li>)}</ul>
          <h2>Direitos de aprendizagem da Educação Infantil</h2>
          <ul>{(data.earlyChildhoodRights ?? []).map((item) => <li key={item.id}><strong>{item.name}.</strong> {item.text}</li>)}</ul>
          <h2>Competências do complemento de Computação</h2>
          <ul>{(data.computingCompetencies ?? []).map((item) => <li key={item.id}>{item.text}</li>)}</ul>
        </>
      )}
    </Remote>
  );
}
