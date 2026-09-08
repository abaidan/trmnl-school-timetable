#!/usr/bin/env python3
"""Builds the TRMNL private-plugin ZIP from src/."""
import re, sys, zipfile, pathlib, yaml

SRC = pathlib.Path(__file__).parent
OUT = SRC.parent
prep = (SRC / "_prep.liquid").read_text()
today = (SRC / "_today.liquid").read_text()
full = (SRC / "full.liquid").read_text()

views = {
    "full.liquid": prep + "\n" + full,
    "half_vertical.liquid": prep
        + '\n{%- assign tt_size = "table--small lg:table--base" -%}'
        + '\n{%- assign tt_subj_size = "lg:label--large" -%}'
        + '\n{%- assign tt_show_room = show_room -%}\n' + today,
    "half_horizontal.liquid": prep
        + '\n{%- assign tt_size = "table--xsmall lg:table--small" -%}'
        + '\n{%- assign tt_subj_size = "" -%}'
        + '\n{%- assign tt_show_room = show_room -%}'
        + '\n{%- assign tt_skip_empty = true -%}\n' + today,
    "quadrant.liquid": prep
        + '\n{%- assign tt_size = "table--xsmall lg:table--small" -%}'
        + '\n{%- assign tt_subj_size = "" -%}'
        + '\n{%- assign tt_show_room = false -%}'
        + '\n{%- assign tt_skip_empty = true -%}\n' + today,
}

# --- checks ---
settings_text = (SRC / "settings.yml").read_text()
settings = yaml.safe_load(settings_text)
assert settings["strategy"] == "static"
keys = [f["keyname"] for f in settings["custom_fields"]]
assert len(keys) == len(set(keys)), "duplicate keynames"
print("settings.yml OK, fields:", ", ".join(keys))

OPEN = {"if": "endif", "for": "endfor", "case": "endcase", "capture": "endcapture",
        "unless": "endunless", "comment": "endcomment"}
CLOSE = {v: k for k, v in OPEN.items()}
def check(name, text):
    stack = []
    for m in re.finditer(r"{%-?\s*(\w+)", text):
        tag = m.group(1)
        if tag in OPEN:
            stack.append(tag)
        elif tag in CLOSE:
            if not stack or stack[-1] != CLOSE[tag]:
                sys.exit(f"{name}: unexpected {tag} (stack={stack})")
            stack.pop()
        elif tag in ("when", "else", "elsif", "continue", "break"):
            if not stack: sys.exit(f"{name}: {tag} outside block")
    if stack: sys.exit(f"{name}: unclosed {stack}")
    # variables that are used but never assigned in prep
    used = set(re.findall(r"{{-?\s*([a-z_]+)", text))
    assigned = set(re.findall(r"assign\s+([a-z_]+)", text)) | {"forloop"}
    loopvars = set(re.findall(r"for\s+([a-z_]+)\s+in", text))
    missing = used - assigned - loopvars
    if missing: print(f"  {name}: WARN unassigned: {missing}")
    print(f"{name}: tags balanced, {len(text)//1024} KB")

for n, t in views.items():
    check(n, t)

zpath = OUT / "trmnl-school-timetable.zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("settings.yml", settings_text)
    for n, t in views.items():
        z.writestr(n, t)
print("->", zpath.name)
