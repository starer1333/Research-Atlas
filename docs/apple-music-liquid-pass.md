# Apple Music / Liquid Glass UI Pass

This pass intentionally studies the user-provided Apple Music references more literally than Visual System 1.0.

## Fixed tonal scenes

Colors are tied to product surfaces, never to company or industry.

Reference colors sampled from the screenshots:

| Scene | Main canvas | Sidebar |
|---|---:|---:|
| Blue / Teen Pop | `#4688C2` | `#18527E` |
| Gold / Breaking Pop | `#D6A63F` | `#EAC380` |
| Lavender / Film Score | `#C3B0E2` | `#E5D1FB` |
| Deep teal / Kids TV | `#2E6B63` | `#144840` |
| Green / As Heard on TV | `#80B563` | `#ADE191` |
| Mint / Viral Syncs | `#6BDB88` | `#82EA9E` |

Product mapping:

- Research → Blue
- Evidence → Deep teal
- Analysis / Financials → Lavender
- Analysis / Business → Green
- Analysis / Peers → Mint
- Analysis / Scenario → Gold
- Report → Gold

The mapping is fixed across companies.

## Interaction study

The implementation borrows four ideas from Apple's current Liquid Glass guidance:

1. Glass is a **functional navigation/control layer**, not a background effect on every piece of content.
2. Controls use translucent fill, blur, inner highlights, soft edge definition and responsive scaling.
3. Content remains visually dominant underneath the glass.
4. Transitions are continuous, spring-like and interruptible where the browser supports View Transitions.

## Shape language

- Search / segmented controls: 14–16 px radius
- Navigation platters: 14 px
- Next Step / glass groups: 18 px
- Evidence drawer / strongest overlay: 28 px
- Buttons: rounded 11–14 px, pills only for compact status controls

## Blur / glass

- Sidebar: 30 px blur + saturation
- Top bar: 28 px blur
- Search / selected navigation / segmented controls: 22–24 px blur
- Evidence drawer: 38 px blur
- Backdrop: 12 px blur

Each glass surface also uses an inner top highlight and low-contrast bottom edge so it feels optically layered rather than merely transparent.

## Motion

- Scene color transition: ~520 ms
- Navigation/control transform: ~280–340 ms
- Content entrance: ~420 ms
- View Transition API is used when available
- `prefers-reduced-motion` remains respected

## Boundary

This is a UI pass only. It does not change evidence semantics, calculations, diagnostics, peer comparability, AI boundaries, research memory or other project logic.
