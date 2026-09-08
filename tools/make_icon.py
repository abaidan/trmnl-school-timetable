#!/usr/bin/env python3
"""Generates the plugin icon: assets/icon.svg plus PNG renders.

One set of geometry constants drives both outputs, so the vector and the
raster can't drift apart. The shape is a timetable grid with one column
left solid — the same "today is highlighted" idea the plugin renders on
screen. Pure black on transparency, no gradients or hairlines, so it
survives being shrunk to the ~24px of the title bar and stays legible on
a 1-bit display.

It is drawn as a filled rounded square with the empty cells knocked out
of it, so the frame, the header bar and the grid lines are all just the
gaps left behind. That keeps the outline mathematically perfect: nothing
is ever painted near the corners, and the knockouts are clipped to the
inner curve so the bottom row follows it.
"""
import base64, math, pathlib, re, struct, zlib

S = 512.0            # canvas
PAD = 30.0           # margin around the frame
BORDER = 18.0        # frame stroke, i.e. the gap left around the cells
RADIUS = 92.0        # outer corner radius
HEADER = 62.0        # height of the solid header bar
GRID = 15.0          # gap between cells
COLS, ROWS = 4, 3    # body grid
TODAY = 1            # 0-based column left solid

X0, Y0, X1, Y1 = PAD, PAD, S - PAD, S - PAD
IN0, IN1 = X0 + BORDER, X1 - BORDER
IN_R = max(RADIUS - BORDER, 0.0)
BODY_TOP = Y0 + BORDER + HEADER
BODY_BOT = Y1 - BORDER
COL_W = (IN1 - IN0) / COLS
ROW_H = (BODY_BOT - BODY_TOP) / ROWS


def holes():
    """Cells knocked out of the solid square, as (x0, y0, x1, y1)."""
    out = []
    for c in range(COLS):
        if c == TODAY:
            continue
        for r in range(ROWS):
            out.append((
                IN0 + c * COL_W + GRID / 2, BODY_TOP + r * ROW_H + GRID / 2,
                IN0 + (c + 1) * COL_W - GRID / 2, BODY_TOP + (r + 1) * ROW_H - GRID / 2,
            ))
    return out


def svg():
    n = lambda v: f"{v:g}"
    cells = "".join(
        f'<rect x="{n(x0)}" y="{n(y0)}" width="{n(x1 - x0)}" height="{n(y1 - y0)}"/>'
        for x0, y0, x1, y1 in holes()
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n(S)} {n(S)}" '
        f'width="{n(S)}" height="{n(S)}">'
        f'<defs><clipPath id="i"><rect x="{n(IN0)}" y="{n(Y0 + BORDER)}" '
        f'width="{n(IN1 - IN0)}" height="{n(BODY_BOT - Y0 - BORDER)}" rx="{n(IN_R)}"/>'
        f'</clipPath>'
        f'<mask id="m"><rect width="{n(S)}" height="{n(S)}" fill="#fff"/>'
        f'<g clip-path="url(#i)" fill="#000">{cells}</g></mask></defs>'
        f'<rect x="{n(X0)}" y="{n(Y0)}" width="{n(X1 - X0)}" height="{n(Y1 - Y0)}" '
        f'rx="{n(RADIUS)}" fill="#000" mask="url(#m)"/></svg>'
    )


def _round_span(y, x0, y0, x1, y1, r):
    """Horizontal span of a rounded rect at scanline centre y, or None."""
    if y < y0 or y > y1:
        return None
    d = 0.0
    if y < y0 + r:
        d = r - math.sqrt(max(r * r - (y0 + r - y) ** 2, 0))
    elif y > y1 - r:
        d = r - math.sqrt(max(r * r - (y - (y1 - r)) ** 2, 0))
    return x0 + d, x1 - d


def raster(size, ss=4):
    """Scanline-rasterise at ss x and box-filter down to `size`."""
    w = size * ss
    k = w / S
    rows = [bytearray(w) for _ in range(w)]
    sc = lambda *v: tuple(x * k for x in v)

    ox0, oy0, ox1, oy1, orad = sc(X0, Y0, X1, Y1, RADIUS)
    ix0, iy0, ix1, iy1, irad = sc(IN0, Y0 + BORDER, IN1, BODY_BOT, IN_R)
    cells = [sc(*h) for h in holes()]

    for y in range(w):
        cy = y + 0.5
        outer = _round_span(cy, ox0, oy0, ox1, oy1, orad)
        if not outer:
            continue
        a, b = max(0, math.ceil(outer[0] - 0.5)), min(w, math.ceil(outer[1] - 0.5))
        if b <= a:
            continue
        rows[y][a:b] = b"\xff" * (b - a)

        inner = _round_span(cy, ix0, iy0, ix1, iy1, irad)
        if not inner:
            continue
        for hx0, hy0, hx1, hy1 in cells:
            if cy < hy0 or cy > hy1:
                continue
            ca = max(math.ceil(max(hx0, inner[0]) - 0.5), 0)
            cb = min(math.ceil(min(hx1, inner[1]) - 0.5), w)
            if cb > ca:
                rows[y][ca:cb] = b"\x00" * (cb - ca)

    alpha = bytearray(size * size)
    for y in range(size):
        base = y * ss
        for x in range(size):
            t = 0
            for dy in range(ss):
                t += sum(rows[base + dy][x * ss:x * ss + ss])
            alpha[y * size + x] = t // (ss * ss)
    return alpha


def png(alpha, size, path):
    raw = bytearray()
    for y in range(size):
        raw.append(0)                                  # filter: none
        for x in range(size):
            raw += b"\x00\x00\x00" + bytes([alpha[y * size + x]])

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parent.parent
    out = root / "assets"
    out.mkdir(exist_ok=True)
    markup = svg()
    (out / "icon.svg").write_text(markup)
    print(f"icon.svg {len(markup)} bytes")
    for n in (512, 128, 48):
        png(raster(n), n, out / f"icon-{n}.png")
        print(f"icon-{n}.png")

    # keep the title-bar copy in step with the file; inlined so the plugin
    # doesn't depend on fetching an image at render time
    uri = "data:image/svg+xml;base64," + base64.b64encode(markup.encode()).decode()
    prep = root / "src" / "_prep.liquid"
    text = prep.read_text()
    patched, n = re.subn(r'(\{%- assign tt_icon = ")[^"]*(" -%\})',
                         lambda m: m.group(1) + uri + m.group(2), text)
    if n:
        prep.write_text(patched)
        print(f"_prep.liquid tt_icon updated ({len(uri)} chars)")
    else:
        print("WARN: no tt_icon assign found in src/_prep.liquid")
