import { useEffect, useRef, useState } from "preact/hooks";
import type { Result } from "./types";

const base = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
export const DISPLAY_REFRESH_MS = 5000;
export function useApi<T>(path: string | null, interval = DISPLAY_REFRESH_MS) {
  const [result, setResult] = useState<Result<T> | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [reload, setReload] = useState(0);
  const current = useRef(path);
  useEffect(() => {
    current.current = path;
    setResult(null);
    setError("");
    setLoading(Boolean(path));
    if (!path) return;
    let alive = true,
      busy = false;
    const controller = new AbortController();
    const get = async () => {
      if (busy || !alive || document.hidden) return;
      busy = true;
      try {
        const response = await fetch(`${base}${path}`, {
          signal: controller.signal,
          headers: { Accept: "application/json" },
        });
        if (!response.ok)
          throw new Error(
            response.status === 404
              ? "No encontramos esos datos."
              : "No pudimos conectar con los resultados.",
          );
        if (!response.headers.get("content-type")?.includes("application/json"))
          throw new Error("El servicio de resultados todavía no está disponible.");
        const body = (await response.json()) as Result<T>;
        if (!("data" in body) || !body.meta)
          throw new Error("La API no devolvió datos válidos.");
        if (alive) {
          setResult(body);
          setError("");
        }
      } catch (e) {
        if (alive && !(e instanceof DOMException && e.name === "AbortError"))
          setError(e instanceof Error ? e.message : "Error de conexión");
      } finally {
        busy = false;
        if (alive) setLoading(false);
      }
    };
    void get();
    const timer = interval
      ? window.setInterval(() => void get(), interval)
      : undefined;
    const visible = () => {
      if (!document.hidden) void get();
    };
    document.addEventListener("visibilitychange", visible);
    return () => {
      alive = false;
      controller.abort();
      clearInterval(timer);
      document.removeEventListener("visibilitychange", visible);
    };
  }, [path, interval, reload]);
  return {
    result: current.current === path ? result : null,
    loading: current.current !== path || loading,
    error,
    retry: () => setReload((x) => x + 1),
  };
}
