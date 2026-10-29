"use client";

import Link from "next/link";
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
          <p className="crumb"><Link href={`/anos/${params.gradeId}`}>{data.gradeLabel}</Link></p>
          <h1>{(data.subject as { name: string }).name}</h1>
          <Timeline gradeId={params.gradeId} subject={data.subject} initialTopicId={search.get("topico") ?? undefined} />
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
