"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export function Remote<T>({ path, children }: { path: string; children: (data: T) => React.ReactNode }) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    api<T>(path).then((value) => {
      if (!cancelled) setData(value);
    }).catch(() => {
      if (!cancelled) setError("Não foi possível carregar os dados. Deixe a API em execução na porta 8000.");
    });
    return () => { cancelled = true; };
  }, [path]);
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p role="status">Carregando…</p>;
  return <>{children(data)}</>;
}
