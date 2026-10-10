import { lazy, type ComponentType, type LazyExoticComponent } from "react";
import type { Bundle } from "../engine/types";

/** Every page, defined once: the nav, the top-bar title and <Routes> all derive from this list. */
export interface PageProps { bundle: Bundle; search: string }
export interface RouteDef {
  path: string;
  label: string;          // nav text
  title: string;          // document title
  bleed?: boolean;        // full-width page (no content padding)
  search?: boolean;       // shows the search box
  needsBundle: boolean;
  Page: LazyExoticComponent<ComponentType<PageProps>>;
}

const page = <T,>(load: () => Promise<T>, pick: (m: T) => ComponentType<PageProps>) =>
  lazy(() => load().then((m) => ({ default: pick(m) })));

export const ROUTES: RouteDef[] = [
  { path: "/", label: "Outlook", title: "Abu Dhabi Hotel Outlook", bleed: true, needsBundle: true,
    Page: page(() => import("../features/landing/LandingPage"), (m) => m.LandingPage) },
  { path: "/simulate", label: "Flight scenarios", title: "Flight scenarios", needsBundle: true,
    Page: page(() => import("../features/simulate/SimulatePage"), (m) => ({ bundle }) => <m.SimulatePage planning={bundle.planning} weekly={bundle.weekly} />) },
  { path: "/nowcast", label: "Daily forecast", title: "Daily hotel guests", search: true, needsBundle: true,
    Page: page(() => import("../features/nowcast/Dashboard"), (m) => m.Dashboard) },
  { path: "/report", label: "How it works", title: "How it works", bleed: true, needsBundle: false,
    Page: page(() => import("../features/report/ReportPage"), (m) => ({ bundle }) => <m.ReportPage manifest={bundle?.manifest ?? null} />) },
];

export const PRIMARY_ACTION = { to: "/simulate", label: "Try a scenario" };
