/** A small inline icon set (24px grid, stroke icons), so no icon library is needed. */
const paths = {
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6L6 18",
  arrow: "M5 12h14M13 6l6 6-6 6",
};

export type IconName = keyof typeof paths | "logo";

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  if (name === "logo") {
    // 706 x 268 aspect ratio (~2.634)
    const height = size;
    const width = Math.round(size * (706 / 268));
    return (
      <img
        src="/logo.svg"
        alt="AeroLodge Metrics logo"
        width={width}
        height={height}
        style={{ display: "inline-block", verticalAlign: "middle", objectFit: "contain" }}
        aria-hidden="true"
      />
    );
  }

  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  );
}
