"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { apiFetch } from "@/lib/api";

/** Hook mínimo de dados: loading/error/refetch, sem dependência externa. */
export function useApiData<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const pathRef = useRef(path);
  pathRef.current = path;

  const refetch = useCallback(async () => {
    const current = pathRef.current;
    if (current === null) return;
    setLoading(true);
    setError(null);
    try {
      setData(await apiFetch<T>(current));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Erro ao carregar");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refetch();
  }, [path, refetch]);

  return { data, error, loading, refetch };
}

export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}
