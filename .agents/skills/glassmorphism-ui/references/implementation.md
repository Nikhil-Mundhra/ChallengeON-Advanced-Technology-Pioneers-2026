# Implementing glass per stack

The recipe in `SKILL.md` is stack-agnostic. This is the mapping. The parts that matter everywhere: opacity ramp, hairline border, inset highlight, worst-case contrast test.

## The capability question, first

Ask before designing: **can this stack blur what is behind the surface?**

| Stack | Backdrop blur | Notes |
|---|---|---|
| CSS / browser | Yes | `backdrop-filter` (+ `-webkit-` for Safari) |
| Compose Multiplatform | **No, not cross-platform** | See below |
| SwiftUI | Partial | `.background(.ultraThinMaterial, in:)` blurs content behind it **within the window**, not OS window content |
| React Native | Yes, via a native module | `@react-native-community/blur`, or `expo-blur` |

Where the answer is no, do not ship fake blur. Do the compensation: **fill opacity up to 80-90%, border up, drop blur from the spec.** A translucent panel with no blur reads as a bug; a near-opaque panel with a strong hairline reads as intentional.

## CSS

```css
.glass-panel {
  background: rgb(255 255 255 / 0.70);
  backdrop-filter: blur(16px) saturate(1.4);
  -webkit-backdrop-filter: blur(16px) saturate(1.4);
  border: 1px solid rgb(255 255 255 / 0.18);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgb(0 0 0 / 0.08), inset 0 1px 0 rgb(255 255 255 / 0.15);
}
```

Rules:

- Always include the `-webkit-` prefix. Safari needs it; other browsers ignore it.
- Gate with `@supports not (backdrop-filter: blur(1px))` and ship the opaque fallback — there is no reason to detect blur at runtime beyond this.
- `saturate(1.4)` goes in the same declaration as the blur. Without it, the backdrop goes grey and the glass looks dirty rather than crisp.
- `will-change: backdrop-filter` promotes the element and can help or hurt depending on the browser; measure before adding it.

Performance: a full-viewport backdrop-filter repaints on every scroll frame. On long pages, prefer `position: sticky` panels over fixed ones, and never put backdrop-filter on more than a few elements at once.

## Tailwind

`backdrop-blur-*` maps to Tailwind's scale, which lines up closely with the tiers:

| Class | Blur | Tier |
|---|---|---|
| `backdrop-blur-sm` | 4px | below the floor — do not use |
| `backdrop-blur-md` | 8px | Light |
| `backdrop-blur-lg` | 16px | Medium |
| `backdrop-blur-xl` | 24px | Heavy |
| `backdrop-blur-2xl` | 40px | past the heavy tier |

Compose the fill and border from the token file as arbitrary values (`bg-white/70`, `border-white/20`). Defining the whole ramp in the theme file is better than repeating these classes — then the ramp is enforced by one place.

```css
/* tailwind v4 @theme */
@theme {
  --color-glass-fill-panel: rgb(255 255 255 / 0.70);
  --color-glass-border: rgb(255 255 255 / 0.18);
}
```

## Compose Multiplatform

Compose has **no cross-platform backdrop blur**. Per platform:

- **Desktop JVM** — nothing built in. Either composite your own blurred snapshot of the scene behind the window, or accept the no-blur compensation rule above. This is the usual outcome.
- **Android** — `Modifier.blur()` blurs the element's *own content*, not what is behind it, and only renders properly on API 31+. It is not a backdrop blur. For a true backdrop effect, use a `RenderEffect` (API 31+) against a captured snapshot.
- **iOS** — no Compose API; drop to `UIVisualEffectView` via `UIKitView`.
- **WASM/web** — use the CSS recipe.

Because of this, the practical Compose implementation of the recipe is the **no-blur compensation**: translucent gradient fill, gradient stroke, soft shadow. That is exactly the path the upstream `kmp-glassmorphism-skill` takes, which is why its components are built on translucent gradients and gradient borders rather than real blur.

```kotlin
Box(
    modifier = Modifier
        .clip(shape)
        .background(
            Brush.verticalGradient(
                listOf(surfaceVariant.copy(alpha = alpha), surface.copy(alpha = alpha))
            )
        )
        .border(
            Brush.linearGradient(
                0.0f to Color.White.copy(alpha = 0.55f),
                1.0f to Color.White.copy(alpha = 0.12f),
            ),
            shape,
        )
)
```

Keep the alpha ramp and the border weight identical to the CSS build so the two stay one system.

## SwiftUI

```swift
.padding(16)
.background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
.overlay(
    RoundedRectangle(cornerRadius: 16)
        .strokeBorder(Color.white.opacity(0.18), lineWidth: 1)
)
.shadow(color: .black.opacity(0.08), radius: 16, y: 8)
```

- `strokeBorder` rather than `stroke` — `stroke` inflates the shape and shifts layout by half the line width.
- `.ultraThinMaterial` is the closest to the Light tier; `.regularMaterial` and `.thickMaterial` step up. There is no direct blur-radius control.
- Materials do not blur across separate windows or over other apps' content.
- Respect reduce-motion and reduce-transparency through the environment values rather than by querying system settings directly.

## React Native

```jsx
import { BlurView } from '@react-native-community/blur';

<BlurView blurType="light" blurAmount={16} reducedTransparencyFallbackColor="#F0F2F5" style={styles.panel} />
```

- `reducedTransparencyFallbackColor` is the accessibility hook — it is what iOS uses when Reduce Transparency is on. Set it explicitly; do not let it default.
- `blurType` is a coarse enum (`light`/`dark`/`xlight`), not a pixel radius. Approximate the tiers: `light` ≈ Light, `dark`/`xlight` ≈ Heavy.
- Add the fill and border on top of the BlurView; it only supplies the blur.
- Android support is weaker than iOS. Verify on device; the no-blur compensation is the fallback.

## Verification, any stack

1. Render over the busiest background in the product. If there isn't one, add one temporarily — a glass UI with a plain background behind it has not been tested.
2. Check body text contrast (4.5:1) over that background, not over a neutral swatch.
3. Tab through every interactive surface. The focus ring must stay visible and must not be clipped by a layer above it.
4. Toggle reduced-motion and reduced-transparency. Both must degrade to something readable.
5. Scroll a long page and watch frame rate if the surface is `fixed` or full-height.