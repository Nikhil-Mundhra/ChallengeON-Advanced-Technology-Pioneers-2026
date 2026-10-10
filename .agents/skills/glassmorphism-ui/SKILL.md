---
name: glassmorphism-ui
description: Framework-agnostic rules for building frosted-glass (glassmorphism) interfaces. Use when asked for glass UI, frosted panels, translucent or blurred surfaces, layered depth, or a liquid/blob animated background. Covers blur tiers, alpha ramps, border recipes, layer stacking, component states, and WCAG 2.2 AA safeguards. Applies to CSS, Compose, SwiftUI, and React Native; not to one stack.
---

# Glassmorphism UI

Translucent panels that read as panes of frosted glass floating over a rich background. The effect is a **spatial** device: it tells the user what sits on top of what.

Two rules govern everything below:

1. **Glass is structural, not decorative.** Every translucent surface encodes a layer relationship. A panel sits above content, a modal floats above panels, a tooltip floats above everything. If a surface is not expressing a z-relationship, make it opaque.
2. **Legibility outranks the look.** When the frosted aesthetic and readability disagree, the frosted aesthetic loses. Every value here was chosen to keep text readable over the *worst-case* background, not the prettiest one.

## When to use

Messaging and chat interfaces, dashboards and live-monitoring surfaces, media and creative tools, overlay stacks (modals, drawers, command palettes), navigation chrome.

Skip it for: long-form reading surfaces, dense data tables where a grid must stay scannable, body text over photography, and any surface where the background is plain white or a single flat color. Glass needs something to refract. On a flat background it reads as accidental transparency.

Do not mix with competing metaphors — neobrutalism, flat Material, skeuomorphism. Translucency only reads as depth if nothing else in the system is claiming depth.

## The glass recipe

A glass surface is **five** stacked things, in order. Missing any one is what makes fake glass look cheap.

| Layer | Purpose | Value |
|---|---|---|
| 1. Backdrop blur | Softens what shows through, focusing attention on the content in front | 8-32px, see tiers below |
| 2. Saturate | Stops the blur from washing out colour | `saturate(1.4)` alongside blur |
| 3. Translucent fill | Tints toward the surface colour, sets contrast floor | 60-80% opacity |
| 4. Hairline border | The edge-light that makes the pane read as a physical edge | 1px `rgba(255,255,255,0.18)` |
| 5. Shadow | Lifts the pane off its neighbour | Large, very soft, low opacity |

Rules for composing them:

- The border is **light on the top edge, weaker on the bottom**, or a uniform hairline in dark mode. A flat 1px border is the single most common tell of an unconvincing glass panel.
- Add an inset top highlight (`inset 0 1px 0 rgba(255,255,255,0.15)`) for physicality. Skip it if the surface is large and full-bleed.
- Never stack more than **three** glass layers deep. Beyond that, translucency compounds into mush and the top layer stops being readable.
- Radius: 12-24px for panels, `9999px` for pills and chips.

## Blur tiers

Blur strength is a **readability budget**, not a style setting. Higher blur = more contrast stability.

| Tier | Blur | Use for | Content density |
|---|---|---|---|
| Light | 8-12px | Chips, small badges, inline toolbars, hover cards | Sparse |
| Medium | 16-20px | Panels, cards, sidebars, dropdown menus | Moderate |
| Heavy | 24-32px | Modals, drawers, sheets, command palettes | Dense or unscannable background |

Rules:

- **Higher layer = heavier blur.** A modal over a blurred panel needs *more* blur than the panel, not less, or its own content competes with the layer beneath.
- **Never put dense text at the light tier.** Small body copy over a 8px blur over a busy image is the failure case.
- Blur costs GPU. A full-screen backdrop-filter repaints every frame. Prefer animating `transform` and `opacity` only; never animate `backdrop-filter` itself.
- When the runtime cannot blur the backdrop (see [references/implementation.md](references/implementation.md)), compensate by raising fill opacity toward 80-90% and strengthening the border. Faked glass needs less transparency, not more.

## Alpha ramp

| Role | Opacity |
|---|---|
| Small chip, badge, hover card | 60% |
| Panel, card, sidebar | 70% |
| Dropdown, popover, tooltip | 80% |
| Modal, drawer, sheet | 90% |

Fill opacity and blur move together: as blur drops, fill opacity rises. Never ship a transparent fill with no blur behind it.

## Background dependency

The effect requires a visually rich background — a gradient, an image, or layered colour. If the surface underneath is plain:

- Introduce a soft radial gradient or two low-contrast colour blooms behind the content.
- If the page genuinely cannot carry a background (print, dense tables, white-label embedding), **fall back to opaque surfaces.** Do not ship translucent-on-white; it looks broken and it fails contrast.

## Component states

Every interactive glass component needs these states, and each needs an explicit treatment — do not let them fall out of the framework default.

| State | Treatment |
|---|---|
| Default | Base fill + hairline border |
| Hover | **Opacity shift only** (+5-10% fill), never a background colour swap |
| Focus-visible | **Solid 2px ring**, 2px offset, high-contrast colour — never translucent |
| Active | Opacity down 5% |
| Disabled | Opacity down to 40%, remove border, `cursor: not-allowed` |
| Loading | Preserve the component's box, replace contents with a spinner at 60% opacity |
| Error | Keep the glass; add a 1px error-coloured border and an icon. Do not swap to a solid red block |

The hover rule matters most: on a translucent surface, a background colour swap reads as a different component. Shift opacity, or shift the border.

## Accessibility

Glassmorphism is one of the higher-risk visual styles precisely because contrast depends on what is behind it. Treat these as gates, not suggestions.

- **Contrast floor.** Body text must hold 4.5:1 (WCAG 2.2 SC 1.4.3; 3:1 for text >= 18.66px bold or 24px) against its *worst-case* backdrop, not the average one. If the fill alone cannot guarantee it, raise fill opacity or add a scrim.
- **Focus must never be obscured** by the glass stack (SC 2.4.11). Stacked translucent overlays can hide the focused element. Check it.
- **Non-text contrast**: borders, focus rings, and control boundaries need 3:1 against their adjacent colour (SC 1.4.11). A `rgba(255,255,255,0.18)` border is decorative and exempt — but a focus ring is not.
- **Reduced motion is mandatory.** Any blob drift, parallax, or layer animation must respect `prefers-reduced-motion: reduce`. Ship the motion gated behind the media query, not just documented as optional.
- **Reduced transparency.** Provide an opaque or near-opaque mode for users who ask for it, and honour it via media query where the platform allows.
- **Worst-case background test.** Before shipping, render the surface over: the busiest image, the most saturated gradient, pure white, and pure black. If text fails on any, the fill opacity is too low.

## Decision tree

1. **Does the surface express a layer relationship?** No → make it opaque.
2. **Can the runtime blur the backdrop?** No → see the compensation note above.
3. **Is the background rich enough?** No → add a gradient, or fall back to opaque.
4. **How much text is on it?** Sparse → Light tier. Dense → Heavy tier.
5. **Does it carry interaction?** Then it needs all seven states, with a solid focus ring.

## Anti-patterns

- Translucent text, or text at low opacity on glass. Text is either opaque or it is a bug.
- Glass where there is no depth to express — a full-page background "panel".
- More than three stacked glass layers.
- Blur so strong the content behind becomes an indistinct smear (it stops communicating context).
- Animating `backdrop-filter`, `filter`, or `box-shadow`.
- Equal alpha on every surface. The ramp is what creates hierarchy; flattening it is what makes glass look grey.
- Blur with no border. The hairline is what sells the pane edge.

## References

- [references/tokens.md](references/tokens.md) — blur/alpha ramps as CSS custom properties, plus two ready-made palettes to drop in.
- [references/implementation.md](references/implementation.md) — how to realize the recipe in CSS, Tailwind, Compose, SwiftUI, and React Native, and what to do when the platform cannot blur a backdrop.

## Sources

Synthesised from two public references, cited rather than reproduced:

- `Aks-4125/kmp-glassmorphism-skill` (MIT) — component set, alpha ramp, layered-surface approach. Upstream ships Compose source; the generic layer here is an independent rewrite. MIT text in [LICENSE.upstream](LICENSE.upstream).
- [TypeUI glassmorphism design skill](https://www.typeui.sh/design-skills/glassmorphism) — blur intensity tiers, fill and border values, `saturate` guidance, accessibility position. Their full skill file is behind a login or their `npx typeui.sh pull glassmorphism` CLI and is **not** reproduced here.