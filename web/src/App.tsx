import { Suspense, useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router";
import { PRIMARY_ACTION, ROUTES } from "./app/routes";
import { Icon } from "./components/layout/icons";
import { TopNav } from "./components/layout/TopNav";
import "./components/layout/layout.css";
import { loadBundle } from "./data/bundle";
import type { Bundle } from "./engine/types";

/** One bundle load for every page; pages render only from it (no API). */
function Routed() {
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const { pathname } = useLocation();
  const route = ROUTES.find((r) => r.path === pathname);
  useEffect(() => { loadBundle().then(setBundle, (e: Error) => setError(e.message)); }, []);
  useEffect(() => { window.scrollTo(0, 0); document.title = route?.title ?? "Abu Dhabi Hotel Outlook"; }, [pathname, route]);

  const searchBox = route?.search && (
    <label className="topnav__search">
      <Icon name="search" size={14} />
      <span className="visually-hidden">Search nationalities</span>
      <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search nationalities" />
    </label>
  );
  const loading = <p className="note" aria-live="polite">Loading…</p>;

  return (
    <div className="app">
      <TopNav items={ROUTES.map((r) => ({ to: r.path, label: r.label }))} action={PRIMARY_ACTION} extra={searchBox} />
      <main className={`content${route?.bleed ? " content--bleed" : ""}`}>
        {error && <p role="alert">{error}</p>}
        <Suspense fallback={loading}>
          <Routes>
            {ROUTES.map(({ path, Page, needsBundle }) => (
              <Route key={path} path={path}
                     element={needsBundle && !bundle ? loading : <Page bundle={bundle as Bundle} search={search} />} />
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
