"use client";

import { useParams, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Remote } from "@/components/Remote";
import { Timeline } from "@/components/Timeline";

function SubjectBody() {
  const params = useParams<{ gradeId: string; subjectId: string }>();
  const search = useSearchParams();
  return (
    <Remote<{ gradeLabel: string; subject: never; sequenceNote: string }> path={`/api/grades/${params.gradeId}/subjects/${params.subjectId}`}>
      {(data) => (
        <>
          <p>{data.gradeLabel}</p>
          <h1>{(data.subject as { name: string }).name}</h1>
          <Timeline gradeId={params.gradeId} subject={data.subject} sequenceNote={data.sequenceNote} initialTopicId={search.get("topico") ?? undefined} />
        </>
      )}
    </Remote>
  );
}

export default function SubjectPage() {
  return (
    <Suspense fallback={<p role="status">Carregando…</p>}>
      <SubjectBody />
    </Suspense>
  );
}
