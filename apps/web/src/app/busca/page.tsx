"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

function RedirectToLanding() {
  const params = useSearchParams();
  const router = useRouter();
  useEffect(() => {
    const query = params.get("q");
    router.replace(query ? `/?q=${encodeURIComponent(query)}` : "/");
  }, [params, router]);
  return <p role="status">Abrindo a busca…</p>;
}

export default function SearchPage() {
  return (
    <Suspense fallback={<p role="status">Abrindo a busca…</p>}>
      <RedirectToLanding />
    </Suspense>
  );
}
