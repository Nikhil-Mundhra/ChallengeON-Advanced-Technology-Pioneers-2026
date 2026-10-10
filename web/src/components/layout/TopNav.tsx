import { useEffect, useState, type ReactNode } from "react";
import { Link, NavLink, useLocation } from "react-router";
import { Icon } from "./icons";

export interface NavEntry { to: string; label: string }

/** Fixed top bar: brand, pill links (the current page is a white pill), one primary action. On small
 *  screens the links drop down as a sheet under the bar. */
export function TopNav({ items, action, extra }: { items: NavEntry[]; action: NavEntry; extra?: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => setOpen(false), [pathname]);
  return (
    <header className={`topnav${open ? " topnav--open" : ""}`}>
      <div className="topnav__inner">
        <Link to="/" className="topnav__brand"><Icon name="logo" size={22} /><span>Abu Dhabi Hotel Outlook</span></Link>
        <nav className="topnav__links" aria-label="Pages">
          {items.map((item) => <NavLink key={item.to} to={item.to} end className="topnav__link">{item.label}</NavLink>)}
        </nav>
        <div className="topnav__end">
          {extra}
          <Link to={action.to} className="pill pill--accent topnav__action">{action.label}</Link>
          <button type="button" className="topnav__toggle" aria-label={open ? "Close menu" : "Open menu"} aria-expanded={open} onClick={() => setOpen(!open)}>
            <Icon name={open ? "close" : "menu"} />
          </button>
        </div>
      </div>
    </header>
  );
}
