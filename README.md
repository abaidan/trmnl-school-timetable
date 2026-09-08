# School Timetable — private TRMNL plugin

Manual input, no API. Optimized for TRMNL X (1872×1404, 4-bit), also works on TRMNL OG.

## Installation

1. Build the ZIP: `pip install pyyaml && python3 src/build.py` → produces `trmnl-school-timetable.zip` (or grab a prebuilt one from Releases).
   Then TRMNL → Plugins → **Private Plugin** → **Import new** → pick the ZIP.
2. Open the plugin settings and fill in the form:
   - **Class**, **School year** — used in the header.
   - **Lesson times** — one line per lesson: `8:00-8:45`. A typical Czech schedule is pre-filled by default.
   - **Breaks** (optional) — `2: Long break` → the line appears after the 2nd lesson.
   - **Monday … Friday** — one line per lesson. An empty line or `-` means a free period.
     Room/teacher go after a `|`: `Maths | 204`.
     Use `//` to break a cell across two lines: `Physical // Education`.
   - **After-school activities** (optional) — one line per activity: `Mon | 15:00-16:30 | Football`.
     Day first, then the time, then the name; the time can be dropped (`Mon | Football`).
     Any number per day, at any time.
   - **Grid orientation** — `Days as columns` (default) or `Days as rows (time across the top)`.
3. Save → **Force Refresh** → check the preview in every layout (Full / Half / Quadrant).

## What it shows

| Layout | Contents |
|---|---|
| Full | Mon–Fri week grid in the chosen orientation. Today is highlighted, the current lesson is inverted. After-school activities get their own row (or column) below/next to the lessons. On OG the rooms are hidden in the grid (not enough space), on X they are shown. |
| Half vertical | Today: #, time, subject, room, then an **After school** block if that day has any activities. Current lesson inverted. Free periods are shown as a dash, so the lesson numbers stay continuous. |
| Half horizontal | The same, but tighter: free periods are **dropped** rather than shown, so the numbers can jump (1, 2, 4 …). |
| Quadrant | Today, compact, subjects only, free periods dropped as above, plus the activities block. |

On weekends, Monday is shown instead of "today", marked as "day off".

All grid cells are equal width (fixed table layout) and their contents are centred. On the full
screen the grid is stretched to `height: 100%` so it fills the display instead of sitting in a band
with dead space around it, and the rows share that height out between them.

Don't reach for `vh` to do this. The framework already sizes `.layout` to
`screen − gaps − title bar`, so `100%` is exactly the available area, whereas `vh` measures the
whole viewport — it overshoots, and `data-table-limit` starts silently dropping rows.

**Line breaks.** `//` anywhere in a subject, room, break name or activity name splits it across
lines, and the cell's clamp grows to match so nothing is truncated:

```
Mon | BigWall // 16:00     →   BigWall
                               16:00

Physical // Education      →   Physical
                               Education
```

Without a `//` the text stays clamped to a single line, so long names are still cut off rather than
reflowing — put the break where you want it.

**Grid orientation.** `Days as columns` is the classic view: days across the top, lesson number and
time down the side, breaks shown as their own row. `Days as rows` flips it — days down the side,
lesson number and time across the top, which fits long subject names better. Breaks are only drawn
in the `Days as columns` layout; in the other one the times in the header already show the gaps.

The time comes from the TRMNL account's timezone (`trmnl.user.utc_offset`) — make sure it is set in Account.

## Sources

Inside `src/`, the underscore-prefixed files are the hand-written sources and everything else is
generated — TRMNL ignores the underscored ones:

| File | |
|---|---|
| `_prep.liquid` | shared data preparation, inlined into every view |
| `_full.liquid` | the week grid, both orientations |
| `_today.liquid` | the single-day views |
| `settings.yml` | the settings form (hand-written) |
| `full.liquid`, `half_vertical.liquid`, `half_horizontal.liquid`, `quadrant.liquid` | generated — do not edit |

`python3 src/build.py` rebuilds the ZIP and rewrites the four generated views in place. The prep
block is inlined into each of them because neither a ZIP import nor GitHub Sync guarantees
shared-markup support.

## Icon

`assets/` holds the plugin icon — a timetable grid with one column left solid, the same "today is
highlighted" idea the plugin renders on screen. Black on transparency, no hairlines, so it holds up
both as a marketplace tile and shrunk into the title bar.

| File | Use |
|---|---|
| `icon.svg` | master, 512×512 |
| `icon-512.png` | marketplace listing |
| `icon-128.png`, `icon-48.png` | smaller renders for previewing |

`python3 tools/make_icon.py` regenerates all of them from one set of geometry constants and also
refreshes the inlined copy in `_prep.liquid` that the title bar uses — the plugin embeds it as a
data URI rather than fetching an image at render time. Edit the constants at the top of the script,
not the generated files. Run `python3 src/build.py` afterwards to get it into the views.

## Getting changes into TRMNL

This repo is connected to **GitHub Sync**, so pushing to `main` is enough: TRMNL picks up the push
event and offers to import the changes (Plugins → Private Plugins → the plugin → GitHub Sync in the
right-hand margin). The import is manual — you accept it. Saving in the TRMNL UI pushes the other
way, as commits from `trmnl-sync[bot]`; those land on the generated files, which is why the sources
are kept under separate names.

Run `python3 src/build.py` and commit its output before pushing, or TRMNL will import stale views.

## If you ever want Bakaláři

Full automation via Polling won't work: the API requires `POST /api/login` → token → `GET /api/3/timetable/actual`. You'd need a middleman (a Cloudflare Worker) that serves ready-made JSON. The template would barely change then — only the source of the `mon_arr…fri_arr` arrays.
