import type { ReactNode } from "react";
import { NavLink } from "react-router";
import { Avatar } from "../ui";
import { Icon, type IconName } from "./icons";
import "./layout.css";

export interface NavItem {
  to: string;
  label: string;
  icon: IconName;
}

interface ShellProps {
  nav: NavItem[];
  title: string;
  meta?: ReactNode;
  search?: { value: string; onChange: (value: string) => void; placeholder: string };
  children: ReactNode;
}

/** App frame: icon sidebar (one link per route), top bar (title, optional search, version, avatar), content. */
export function Shell({ nav, title, meta, search, children }: ShellProps) {
  return (
    <div className="shell">
      <nav className="sidebar" aria-label="Sections">
        <span className="sidebar__logo"><Icon name="logo" size={26} /></span>
        {nav.map((item) => (
          <NavLink key={item.to} to={item.to} end className="sidebar__item" title={item.label} aria-label={item.label}>
            <Icon name={item.icon} />
          </NavLink>
        ))}
        <span className="sidebar__spacer" />
      </nav>
      <div className="workspace">
        <header className="topbar">
          <span className="topbar__title">{title}</span>
          {search && (
            <label className="topbar__search">
              <Icon name="search" size={16} />
              <span className="visually-hidden">{search.placeholder}</span>
              <input value={search.value} onChange={(event) => search.onChange(event.target.value)} placeholder={search.placeholder} />
            </label>
          )}
          <div className="topbar__meta">
            {meta}
            <Avatar name="Abu Dhabi DCT" size={32} />
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
