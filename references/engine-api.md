# Engine API (engine/engine.js + theme.css)

Stage = fixed **1920×1080** canvas, scaled to the window. A scene's `.body` area is **1728×780 px** starting at
(96, 202); coordinates inside `.body` are relative to it. Bottom ~100 px of the stage is reserved for captions.

## Scene skeleton
```html
<section class="scene" data-scene="elemente" data-part="3.1 Systemdenken">
  <div class="head">
    <span class="kick" data-at="@start+0.2" data-fx="pop">3.1.1</span>
    <h2 data-at="@start+0.3" data-fx="rise">Titel</h2>
  </div>
  <div class="body"> … absolutely positioned content … </div>
</section>
```
`data-scene` must equal the id in `script.md`. `data-part` fills the chips at the top right (first scene of a part
turns its chip on). Scenes fade in/out over 0.5 s at their window edges (window = lead + speech + gap, set by narrate.py).

## Timing attributes (any element)
| attribute | meaning |
|---|---|
| `data-at="cue"` | start time = the `[cue]` word of this scene. `cue+0.8` / `cue-0.3` offsets in seconds. `other.cue` for another scene, `@start` / `@end` for the scene window. |
| `data-fx` | effect (below). Default `fade` if `data-at` is set. |
| `data-dur` | entrance duration in s (default 0.6; edges 0.8) |
| `data-out="cue"` / `data-outdur` | fade-out at that cue (default 0.4 s) |

Effects: `fade` `rise` `drop` `left` `right` `pop` (scale-in) · `grow` (bar from bottom) `growx` (from left) ·
`wipe` (left→right reveal) `wipey` (top→bottom) · `draw` (SVG stroke; element needs `pathLength="1"`) ·
`edge` (arrow, built by the engine) · `hl` (ring+glow) `hlfill` (ring+glow+tint, uses `--k`) · `dim` · `none`
(only sets `--p`, use your own CSS: `width:calc(var(--p)*60%)`).
Everything is driven by `--p` (0→1 entrance) and `--q` (0→1 exit) on the element and `--t` (global time) /
`--st` (time in scene) on stage/scene – so you can write custom CSS animations that stay scrub-safe.

## Arrows between nodes (auto-routed)
```html
<div class="graph abs" style="left:0;top:0;width:1200px;height:500px">
  <svg class="edges">
    <g class="edge cc" data-edge="a>b" data-at="cue"></g>                    <!-- node ids; clipped to node borders -->
    <g class="edge ca" data-edge="a@bottom>b@top" data-arrow="both"></g>    <!-- sides: @top @bottom @left @right -->
    <g class="edge cd" data-edge="800,325>800,215" data-curve="0.5"></g>     <!-- raw coordinates, curved -->
  </svg>
  <div class="node cc" id="x-a" style="left:0;top:0;width:200px;height:76px" data-at="cue" data-fx="pop">A</div>
</div>
```
Options: `data-arrow="both|none"`, `data-curve` (fraction of length; positive bulges right for upward / left for downward
arrows, negative the other way), `data-pad` (gap to node border, negative hides the line end under the node),
class `dash` for a plain dashed-look line, colour via `cc/ca/cb/cd/ce/cok`.
Nodes must be direct children of `.graph` with `position:absolute` (class `node` does that) and **unique ids**.

## Building-block classes
`.abs` absolute · `.row` `.col` flex · `.center` · `.card` (+ `<h3>`) · `.node` (`.fill` `.ghost`) · `.chip` (`.fill`) ·
`.lbl` small absolute label · `ul.pts` bullet list · colour tokens `ca` amber, `cb` teal, `cc` blue, `cd` coral,
`ce` violet, `cok` green (set `--k`; `tca…` for text colour) · `.mute` `.big` `.sm` `.xs` · SVG: `class="t-mute"`.
Custom CSS per project: `theme.css` next to `script.md` (appended after the engine theme).

## JS hooks (for tools)
`window.__seek(t)` draws time t · `window.__duration` · `window.__cues` · `window.__scenes` · `window.__missing`
(cues missing from timing) · `window.__t()` current time · URL params: `?export=1` hides UI, `?t=12.5` starts there.
Keys: Space play/pause, ←/→ ±5 s, `[` `]` previous/next scene, `c` captions, `f` fullscreen.

## Phones and touch (built into every player)
* **Portrait phones** (width < 820 px): picture on top, captions as large readable text below it, big touch controls underneath, a one-time tip, and a "rotate for a bigger picture" hint.
* **Landscape phones / tablets / desktop:** full-window picture, controls overlay (auto-hide while playing), captions lifted above the controls.
* **Gestures on the picture:** tap = play/pause · double-tap = zoom 2.2× at that spot (again = back) · pinch = zoom (1×–3×) · drag = pan while zoomed. A 🔍 button cycles zoom levels.
* **⛶ Full screen** also asks the browser to lock landscape (works on Android; iPhone can only rotate manually).
* The picture is a fixed 1920×1080 canvas that is scaled; authoring tip: keep body text ≥ 24 px and prefer short bullet lists – on a phone the zoom gesture covers the rest.
* `?export=1` (MP4 export / screenshots) ignores all of this and renders exactly 1920×1080.
