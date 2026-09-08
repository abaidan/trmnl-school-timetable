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
   - **After-school activities** (optional) — one line per activity: `Mon | 15:00-16:30 | Football`.
     Day first, then the time, then the name; the time can be dropped (`Mon | Football`).
     Any number per day, at any time.
   - **Grid orientation** — `Days as columns` (default) or `Days as rows (time across the top)`.
3. Save → **Force Refresh** → check the preview in every layout (Full / Half / Quadrant).

## What it shows

| Layout | Contents |
|---|---|
| Full | Mon–Fri week grid in the chosen orientation. Today is highlighted, the current lesson is inverted. After-school activities get their own row (or column) below/next to the lessons. On OG the rooms are hidden in the grid (not enough space), on X they are shown. |
| Half vertical / horizontal | Today: #, time, subject, room, then an **After school** block if that day has any activities. Current lesson inverted. |
| Quadrant | Today, compact, subjects only (free periods skipped), plus the activities block. |

On weekends, Monday is shown instead of "today", marked as "day off".

All grid cells are equal width (fixed table layout) and their contents are centred.

**Grid orientation.** `Days as columns` is the classic view: days across the top, lesson number and
time down the side, breaks shown as their own row. `Days as rows` flips it — days down the side,
lesson number and time across the top, which fits long subject names better. Breaks are only drawn
in the `Days as columns` layout; in the other one the times in the header already show the gaps.

The time comes from the TRMNL account's timezone (`trmnl.user.utc_offset`) — make sure it is set in Account.

## Sources

`src/` — `settings.yml`, `_prep.liquid` (shared data preparation), `full.liquid`, `_today.liquid`, `build.py`.
`python3 src/build.py` rebuilds the ZIP (the prep block is inlined into every view, because importing a ZIP does not guarantee shared markup support).

## If you ever want Bakaláři

Full automation via Polling won't work: the API requires `POST /api/login` → token → `GET /api/3/timetable/actual`. You'd need a middleman (a Cloudflare Worker) that serves ready-made JSON. The template would barely change then — only the source of the `mon_arr…fri_arr` arrays.
