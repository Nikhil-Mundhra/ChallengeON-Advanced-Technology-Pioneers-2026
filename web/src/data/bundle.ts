import type { Bundle, Manifest } from "../engine/types";

const BASE = `${import.meta.env.BASE_URL}data/`;

async function json<T>(path: string): Promise<T> {
  const response = await fetch(BASE + path);
  if (!response.ok) throw new Error(`Could not load ${path} (${response.status}). Run \`twin export\` first.`);
  return (await response.json()) as T;
}

/** The manifest names the current version; every versioned file is immutable. */
export async function loadBundle(): Promise<Bundle> {
  const manifest = await json<Manifest>("manifest.json");
  if (manifest.schema_version !== 2 && manifest.schema_version !== 3) throw new Error(`Unsupported bundle schema ${manifest.schema_version}`);
  const [nowcast, whatif, planning, weekly, outlook] = await Promise.all([
    json<Bundle["nowcast"]>(manifest.files.nowcast), json<Bundle["whatif"]>(manifest.files.whatif),
    json<Bundle["planning"]>(manifest.files.planning), json<Bundle["weekly"]>(manifest.files.weekly),
    manifest.files.outlook ? json<NonNullable<Bundle["outlook"]>>(manifest.files.outlook) : Promise.resolve(null),
  ]);
  return { manifest, nowcast, whatif, planning, weekly, outlook };
}
