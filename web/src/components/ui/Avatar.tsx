const PALETTE = [1, 2, 3, 4, 5, 6].map((i) => `var(--avatar-${i})`);  // tokens.css

function initials(name: string): string {
  const words = name.replace(/[^A-Za-z ]/g, " ").split(/\s+/).filter(Boolean);
  return (words.length > 1 ? words[0][0] + words[1][0] : name.slice(0, 2)).toUpperCase();
}

function colour(name: string): string {
  let hash = 0;
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

/** A round badge with the name's initials, coloured by a stable hash of the name. */
export function Avatar({ name, size = 36 }: { name: string; size?: number }) {
  return (
    <span className="avatar" aria-hidden="true" title={name}
          style={{ width: size, height: size, background: colour(name), fontSize: size * 0.36 }}>
      {initials(name)}
    </span>
  );
}
