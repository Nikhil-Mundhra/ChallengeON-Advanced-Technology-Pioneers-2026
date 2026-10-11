import { Suspense, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router";
import { PRIMARY_ACTION, ROUTES } from "./app/routes";
import { TopNav } from "./components/layout/TopNav";
import "./components/layout/layout.css";
import { loadBundle } from "./data/bundle";
import type { Bundle } from "./engine/types";

/** One bundle load for every page; pages render only from it (no API). */
function Routed() {
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { pathname } = useLocation();
  const route = ROUTES.find((r) => r.path === pathname);
  useEffect(() => { loadBundle().then(setBundle, (e: Error) => setError(e.message)); }, []);
  useEffect(() => { window.scrollTo(0, 0); document.title = route?.title ?? "Abu Dhabi Hotel Outlook"; }, [pathname, route]);

  const loading = <p className="note" aria-live="polite">Loading…</p>;

  return (
    <div className="app">
      <TopNav items={ROUTES.map((r) => ({ to: r.path, label: r.label }))} action={PRIMARY_ACTION} />
      <main className={`content${route?.bleed ? " content--bleed" : ""}`}>
        {error && <p role="alert">{error}</p>}
        <Suspense fallback={loading}>
          <Routes>
            {ROUTES.map(({ path, Page, needsBundle }) => (
              <Route key={path} path={path}
                     element={needsBundle && !bundle ? loading : <Page bundle={bundle as Bundle} />} />
            ))}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

export function App() {
  return <BrowserRouter><Routed /></BrowserRouter>;
}
