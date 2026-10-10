import { useEffect, useState } from "react";

/** The observed section nearest the reading line. */
export function useActiveId(ids: readonly string[], rootMargin = "-40% 0px -55% 0px"): string {
  const [active, setActive] = useState(ids[0]);
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) setActive(e.target.id);
    }, { rootMargin });
    ids.forEach((id) => { const node = document.getElementById(id); if (node) observer.observe(node); });
    return () => observer.disconnect();
  }, [ids, rootMargin]);
  return active;
}

/** Fade-in on scroll as progressive enhancement: only `.reveal` elements that start below the fold
 *  are hidden (`is-pending`), and each is shown the first time it enters the viewport. Content is
 *  never hidden when the observer is unavailable or never fires for on-screen elements. */
export function useReveal(deps: unknown[] = []) {
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined" || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const below = [...document.querySelectorAll<HTMLElement>(".reveal")].filter((n) => n.getBoundingClientRect().top > window.innerHeight);
    const observer = new IntersectionObserver((entries) => {
      for (const e of entries) if (e.isIntersecting) { e.target.classList.remove("is-pending"); observer.unobserve(e.target); }
    }, { rootMargin: "0px 0px -8% 0px" });
    below.forEach((n) => { n.classList.add("is-pending"); observer.observe(n); });
    return () => { observer.disconnect(); below.forEach((n) => n.classList.remove("is-pending")); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
