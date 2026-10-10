import { lazy, Suspense, useEffect, useState, type ReactElement } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router";
import { Shell, type NavItem } from "./components/layout/Shell";
import { Badge } from "./components/ui";
import { loadBundle } from "./data/bundle";
import type { Bundle } from "./engine/types";
import { ReportPage } from "./features/report/ReportPage";

// Chart pages load on demand, so the report does not download the chart library.
const Dashboard = lazy(() => import("./features/nowcast/Dashboard").then((m) => ({ default: m.Dashboard })));
const SimulatePage = lazy(() => import("./features/simulate/SimulatePage").then((m) => ({ default: m.SimulatePage })));

const NAV: NavItem[] = [
  { to: "/report", label: "Report", icon: "report" },
  { to: "/simulate", label: "Flight scenario simulator", icon: "planning" },
  { to: "/nowcast", label: "Daily guests nowcast", icon: "overview" },
];

const TITLES: Record<string, string> = {
  "/report": "Flights to hotel guests: the report",
  "/simulate": "Flight scenario simulator",
  "/nowcast": "Daily hotel guests nowcast",
};

/** One bundle load for every page; each route renders only from it (no API). */
function Routed() {
  const [bundle, setBundle] = useState<Bundle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const { pathname } = useLocation();
  useEffect(() => { loadBundle().then(setBundle, (e: Error) => setError(e.message)); }, []);
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);

  const meta = bundle && <Badge tone="neutral">model {bundle.manifest.version}</Badge>;
  const searchBox = pathname === "/nowcast" ? { value: search, onChange: setSearch, placeholder: "Search markets or nationalities" } : undefined;
  const ready = (page: (b: Bundle) => ReactElement) => error ? <p role="alert">{error}</p>
    : bundle ? page(bundle) : <p aria-live="polite">Loading the model bundle…</p>;

  return (
    <Shell nav={NAV} title={TITLES[pathname] ?? "Abu Dhabi hotel guests"} meta={meta} search={searchBox}>
      <Suspense fallback={<p aria-live="polite">Loading…</p>}>
      <Routes>
        <Route path="/" element={<Navigate to="/report" replace />} />
        <Route path="/report" element={<ReportPage manifest={bundle?.manifest ?? null} />} />
        <Route path="/simulate" element={ready((b) => <SimulatePage planning={b.planning} weekly={b.weekly} />)} />
        <Route path="/nowcast" element={ready((b) => <Dashboard bundle={b} search={search} />)} />
        <Route path="*" element={<Navigate to="/report" replace />} />
      </Routes>
      </Suspense>
    </Shell>
  );
}

export function App() {
  return <BrowserRouter><Routed /></BrowserRouter>;
}
