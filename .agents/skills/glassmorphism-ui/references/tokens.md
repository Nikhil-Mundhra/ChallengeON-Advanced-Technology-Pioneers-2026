# Glass tokens

Values to drop in. The mechanics section is the part that matters; the palettes are starting points, not defaults.

## Mechanics

```css
:root {
  /* Blur tiers — higher layer = heavier blur */
  --glass-blur-light:  8px;
  --glass-blur-medium: 16px;
  --glass-blur-heavy:  24px;

  /* Fill ramp — opacity rises as blur falls */
  --glass-fill-chip:   0.60;
  --glass-fill-panel:  0.70;
  --glass-fill-overlay: 0.80;
  --glass-fill-modal:  0.90;

  /* Edge light */
  --glass-border:      1px solid rgb(255 255 255 / 0.18);
  --glass-highlight:   inset 0 1px 0 rgb(255 255 255 / 0.15);

  /* Geometry */
  --glass-radius-panel: 16px;
  --glass-radius-card:  24px;
  --glass-radius-pill:  9999px;

  /* Lift — large, soft, low opacity */
  --glass-shadow:
    0 8px 32px rgb(0 0 0 / 0.08),
    0 2px 8px rgb(0 0 0 / 0.04);
}
```

```css
.glass {
  background: rgb(255 255 255 / var(--glass-fill-panel));
  backdrop-filter: blur(var(--glass-blur-medium)) saturate(1.4);
  -webkit-backdrop-filter: blur(var(--glass-blur-medium)) saturate(1.4);
  border: var(--glass-border);
  border-radius: var(--glass-radius-panel);
  box-shadow: var(--glass-shadow), var(--glass-highlight);
}

/* No backdrop-blur support: raise fill opacity rather than dropping the effect. */
@supports not (backdrop-filter: blur(1px)) {
  .glass {
    background: rgb(255 255 255 / 0.92);
    box-shadow: var(--glass-shadow), 0 0 0 1px rgb(0 0 0 / 0.06);
  }
}

@media (prefers-reduced-motion: reduce) {
  .glass, .glass-blob { animation: none; transition: none; }
}
```

## Palette A — Electric

Cool blue primary, muted plum secondary, geometric sans. Suits communication and dashboard products where one interactive element must cut through a busy translucent stack.

| Token | Value | Use |
|---|---|---|
| Primary | `#1856FF` | Primary actions, active state, links |
| Secondary | `#3A344E` | Navigation rails, sidebar grounds, muted surfaces |
| Success | `#07CA6B` | Online status, delivery confirmation |
| Warning | `#E89558` | Pending, soft attention |
| Danger | `#EA2143` | Errors, destructive actions, alerts |
| Surface | `#FFFFFF` | Base from which translucent layers derive |
| Text | `#141414` | Body copy |

Type: **Plus Jakarta Sans** for UI and display, **JetBrains Mono** for timestamps, code, and status identifiers. Both have high x-height and stay legible against a busy backdrop — verify before swapping.

Sourced from the [TypeUI glassmorphism skill](https://www.typeui.sh/design-skills/glassmorphism). Not reproduced from their gated file; values transcribed from its public design page.

## Palette B — Vivid

Purple/cyan on near-black. Higher chroma, reads as more playful; needs a darker ground to avoid the accents vibrating against translucent white.

| Token | Value | Use |
|---|---|---|
| Accent | `#6C63FF` | Primary |
| Accent 2 | `#00E5FF` | Secondary, links, highlights |
| Error | `#FF5252` | Errors |
| Success | `#507652` | Success |
| Background (dark) | `#0A0C14` | Page ground |
| Surface (dark) | `#161922` | Panel ground |
| Background (light) | `#F0F2F5` | Page ground |
| Text (dark) | `#F2F3F7` | Body copy |

Type: system sans-serif. Works without a webfont round-trip, which is often the right call for internal tooling.

Sourced from [`Aks-4125/kmp-glassmorphism-skill`](https://github.com/Aks-4125/kmp-glassmorphism-skill) (MIT).

## Choosing between them

Pick one and derive everything else from it. A glass UI with two competing accents reads as two systems sharing a screen.

- **Palette A** for product UI with dense interactive state — its blue survives being pushed behind three glass layers.
- **Palette B** for dark-first tools and dashboards where the background carries the visual weight.

If the product already has brand tokens, keep those and take only the *mechanics* above. Never restate a hex from this file inside product code — route it through the project's token layer so the glass surfaces stay on the same ramp as everything else.

## Derived values worth checking before shipping

- Blur radius against the **busiest** background actually present, not a neutral gradient.
- Focus ring colour against both the surface and the page ground behind it.
- Text opacity — full opacity only. Translucent text on translucent ground fails contrast in a way no blur setting fixes.