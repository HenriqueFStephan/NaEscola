"use client";

import { useParams } from "next/navigation";
import { LessonView } from "@/components/LessonView";
import { Remote } from "@/components/Remote";

export default function LessonPage() {
  const params = useParams<{ slug: string }>();
  return (
    <Remote<Record<string, unknown>> path={`/api/lessons/${params.slug}`}>
      {(data) => <LessonView payload={data} />}
    </Remote>
  );
}
