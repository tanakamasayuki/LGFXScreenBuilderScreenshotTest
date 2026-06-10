#!/usr/bin/env python3
"""Generate the screenshot gallery (Python stdlib only -- no Node, no deps).

Single source of truth is the generated header (`Sfm.h`): it carries the AI
layout JSON for every scene in a comment block (SPEC §10.2, "Embed AI layouts"
export option). This script parses that block for scene names, descriptions,
profiles, and the per-scene AI JSON, copies the captured PNGs under
docs/shots/<profile>/<scene>.png, and emits two static pages plus a copy-able
AI-layout payload:

  docs/index.html      "By profile"  -- every scene for each profile
  docs/by-scene.html   "By scene"    -- every profile side-by-side per scene
  docs/ai-layouts.js   window.AI_LAYOUTS = { <scene>: <layout> }  (copy buttons)

生成ヘッダ `Sfm.h` を唯一のソースとする（埋め込み AI レイアウトのコメントブロック
= SPEC §10.2）。プロジェクトファイルには依存しない。Python 標準ライブラリのみ。

Usage:
    python3 gen_gallery.py [--header Sfm.h] [--shots screenshot/output] [--out docs]
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# The comment block emitted by the tool (SPEC §10.2). `/` is escaped as `\/`
# inside it, which is valid JSON, so json.loads reads it directly.
BLOCK_RE = re.compile(r"LGFXSB-AI-LAYOUTS v1.*?\n(.*?)\nLGFXSB-AI-LAYOUTS END", re.S)


def find_header(explicit: str | None) -> Path:
    if explicit:
        return (REPO_ROOT / explicit).resolve()
    for h in sorted(REPO_ROOT.glob("*.h")):
        if "LGFXSB-AI-LAYOUTS" in h.read_text(encoding="utf-8", errors="ignore"):
            return h
    raise SystemExit(
        "no header with an embedded AI-layout block found in repo root.\n"
        "Re-export the .h from LGFXScreenBuilder with 'Embed AI layouts' enabled."
    )


def load_model(header_path: Path):
    """Parse the embedded AI-layout block -> (project_name, profiles, scenes, layouts).

    profiles: [{id, w, h, rot}]  (order from the first scene; identical across scenes)
    scenes:   [{id, desc}]
    layouts:  {scene_id: <single-scene AI layout object>}  (for copy buttons)
    """
    text = header_path.read_text(encoding="utf-8")
    m = BLOCK_RE.search(text)
    if not m:
        raise SystemExit(f"{header_path.name}: no LGFXSB-AI-LAYOUTS block")
    doc = json.loads(m.group(1))
    entries = doc.get("scenes", [])
    if not entries:
        raise SystemExit(f"{header_path.name}: embedded block has no scenes")

    name_m = re.search(r"^namespace\s+(\w+)\s*\{", text, re.M)
    name = name_m.group(1) if name_m else header_path.stem

    profiles = [
        {"id": p["id"], "w": int(p["w"]), "h": int(p["h"]), "rot": int(p.get("rot", 0))}
        for p in entries[0].get("profiles", [])
    ]
    scenes = [{"id": e["scene"], "desc": (e.get("desc") or "").strip()} for e in entries]
    layouts = {e["scene"]: e for e in entries}
    return name, profiles, scenes, layouts


def collect_shots(shots_dir: Path, out_dir: Path, profiles, scenes):
    """Copy <profile>__<scene>.png into docs/shots/<profile>/<scene>.png.

    Returns a {(profile_id, scene_id): rel_src} map for the present shots.
    """
    shots_root = out_dir / "shots"
    if shots_root.exists():
        shutil.rmtree(shots_root)
    present: dict[tuple[str, str], str] = {}
    for prof in profiles:
        for scene in scenes:
            src = shots_dir / f"{prof['id']}__{scene['id']}.png"
            if not src.exists():
                continue
            dst = shots_root / prof["id"] / f"{scene['id']}.png"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
            present[(prof["id"], scene["id"])] = f"shots/{prof['id']}/{scene['id']}.png"
    return present


# Light theme on purpose: M5Stack screens are mostly black, so a dark page
# would swallow them. White cards on a light page make each render stand out.
CSS = """
:root { color-scheme: light; --zoom: 2; }
* { box-sizing: border-box; }
body {
  margin: 0; background: #eef1f4; color: #1c2529;
  font: 14px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif;
}
header {
  position: sticky; top: 0; z-index: 10;
  background: #fff; border-bottom: 1px solid #d4dade;
  padding: 12px 20px; display: flex; align-items: baseline; gap: 18px;
}
header h1 { font-size: 16px; margin: 0; color: #11181c; font-weight: 600; }
header .meta { color: #6b7780; font-size: 12px; }
nav { margin-left: auto; display: flex; gap: 6px; }
nav a {
  color: #1f7a74; text-decoration: none; padding: 5px 12px;
  border: 1px solid #1f7a7444; border-radius: 6px;
}
nav a.active { background: #1f7a7415; border-color: #1f7a74; color: #11181c; }
.zoom { color: #6b7780; font-size: 12px; display: flex; align-items: center; gap: 6px; }
.zoom select {
  font: inherit; color: #11181c; background: #fff;
  border: 1px solid #d4dade; border-radius: 6px; padding: 4px 6px;
}
main { padding: 20px; }
section.group { margin: 0 0 36px; }
section.group > h2 {
  font-size: 15px; color: #11181c; margin: 0 0 4px;
  border-left: 3px solid #1f7a74; padding-left: 10px;
  display: flex; align-items: center; gap: 10px;
}
section.group > .sub { color: #6b7780; font-size: 12px; margin: 0 0 14px; padding-left: 13px; }
.row { display: flex; flex-wrap: wrap; gap: 18px; align-items: flex-start; }
.row.stack { flex-direction: column; }  /* by-profile: one image per row */
figure {
  margin: 0; background: #fff; border: 1px solid #d4dade;
  border-radius: 8px; padding: 10px; box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
figure img {
  display: block; background: #000; border-radius: 3px;
  image-rendering: pixelated;
  width: calc(var(--w, 320) * var(--zoom) * 1px);
  height: auto;  /* keep aspect; --zoom (set by the header dropdown) drives size */
}
figcaption {
  margin-top: 8px; color: #1f7a74; font-size: 12px;
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
}
figcaption .dim { color: #6b7780; }
.copy {
  font: inherit; font-size: 11px; cursor: pointer;
  color: #1f7a74; background: #1f7a740f; border: 1px solid #1f7a7455;
  border-radius: 6px; padding: 2px 8px; white-space: nowrap;
}
.copy:hover { background: #1f7a741f; }
.copy.ok { color: #fff; background: #1f7a74; border-color: #1f7a74; }
.empty { color: #c2554f; font-size: 12px; padding: 24px; }
""".strip()


def page(title: str, project: str, generated: str, active: str, body: str) -> str:
    def navlink(href, label, key):
        cls = ' class="active"' if key == active else ""
        return f'<a href="{href}"{cls}>{html.escape(label)}</a>'

    nav = navlink("index.html", "By profile", "profile") + navlink(
        "by-scene.html", "By scene", "scene"
    )
    zoom = (
        '<label class="zoom">Zoom'
        '<select id="zoom">'
        '<option value="1">1x</option>'
        '<option value="2">2x</option>'
        '<option value="3">3x</option>'
        '<option value="4">4x</option>'
        "</select></label>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>{CSS}</style>
<script src="ai-layouts.js"></script>
</head>
<body>
<header>
  <h1>{html.escape(project)} screenshots</h1>
  <span class="meta">generated {html.escape(generated)}</span>
  <nav>{nav}</nav>
  {zoom}
</header>
<main>
{body}
</main>
<script>
(function() {{
  var root = document.documentElement;
  var sel = document.getElementById("zoom");
  var z = localStorage.getItem("shotZoom") || "2";
  root.style.setProperty("--zoom", z);
  sel.value = z;
  sel.addEventListener("change", function() {{
    root.style.setProperty("--zoom", sel.value);
    localStorage.setItem("shotZoom", sel.value);
  }});
  // Copy a scene's AI-layout JSON (one scene x all profiles) to the clipboard.
  document.addEventListener("click", function(ev) {{
    var btn = ev.target.closest(".copy");
    if (!btn) return;
    var data = (window.AI_LAYOUTS || {{}})[btn.dataset.scene];
    if (!data) return;
    navigator.clipboard.writeText(JSON.stringify(data)).then(function() {{
      var prev = btn.textContent;
      btn.textContent = "Copied!"; btn.classList.add("ok");
      setTimeout(function() {{ btn.textContent = prev; btn.classList.remove("ok"); }}, 1200);
    }});
  }});
}})();
</script>
</body>
</html>
"""


def copy_btn(scene_id: str) -> str:
    return (
        f'<button class="copy" data-scene="{html.escape(scene_id)}" '
        f'title="Copy AI layout JSON">⧉ AI JSON</button>'
    )


def img_tag(rel_src: str, prof) -> str:
    # Native size carried via --w; display size = --w * --zoom (header dropdown).
    return (
        f'<img src="{rel_src}" alt="" style="--w:{prof["w"]}" '
        f'width="{prof["w"]}" height="{prof["h"]}" loading="lazy">'
    )


def render_by_profile(profiles, scenes, present, project, generated) -> str:
    out = []
    for prof in profiles:
        rot = f" / rot {prof['rot'] * 90}°" if prof["rot"] else ""
        out.append('<section class="group">')
        out.append(
            f"<h2>{html.escape(prof['id'])}</h2>"
            f'<p class="sub">{prof["w"]}×{prof["h"]}{rot}</p>'
        )
        out.append('<div class="row stack">')
        for scene in scenes:
            rel = present.get((prof["id"], scene["id"]))
            if not rel:
                continue
            out.append(
                "<figure>"
                + img_tag(rel, prof)
                + "<figcaption>"
                + f"<span>{html.escape(scene['id'])}</span>"
                + copy_btn(scene["id"])
                + "</figcaption></figure>"
            )
        out.append("</div></section>")
    if not present:
        out.append('<p class="empty">No screenshots found. Run the capture first.</p>')
    return page(f"{project} screenshots", project, generated, "profile", "\n".join(out))


def render_by_scene(profiles, scenes, present, project, generated) -> str:
    out = []
    for scene in scenes:
        out.append('<section class="group">')
        out.append(
            f"<h2><span>{html.escape(scene['id'])}</span>{copy_btn(scene['id'])}</h2>"
        )
        if scene["desc"]:
            out.append(f'<p class="sub">{html.escape(scene["desc"])}</p>')
        out.append('<div class="row">')
        for prof in profiles:
            rel = present.get((prof["id"], scene["id"]))
            if not rel:
                continue
            dim = f'{prof["w"]}×{prof["h"]}'
            out.append(
                "<figure>"
                + img_tag(rel, prof)
                + f"<figcaption><span>{html.escape(prof['id'])}</span>"
                + f'<span class="dim">{dim}</span></figcaption>'
                + "</figure>"
            )
        out.append("</div></section>")
    if not present:
        out.append('<p class="empty">No screenshots found. Run the capture first.</p>')
    return page(
        f"{project} screenshots by scene", project, generated, "scene", "\n".join(out)
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--header", default=None, help="path to the generated .h")
    ap.add_argument("--shots", default="screenshot/output", help="captured PNG dir")
    ap.add_argument("--out", default="docs", help="output gallery dir")
    args = ap.parse_args()

    header_path = find_header(args.header)
    shots_dir = (REPO_ROOT / args.shots).resolve()
    out_dir = (REPO_ROOT / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    name, profiles, scenes, layouts = load_model(header_path)
    present = collect_shots(shots_dir, out_dir, profiles, scenes)
    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # AI-layout payloads for the copy buttons (loaded by both pages).
    (out_dir / "ai-layouts.js").write_text(
        "window.AI_LAYOUTS = " + json.dumps(layouts, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    (out_dir / "index.html").write_text(
        render_by_profile(profiles, scenes, present, name, generated), encoding="utf-8"
    )
    (out_dir / "by-scene.html").write_text(
        render_by_scene(profiles, scenes, present, name, generated), encoding="utf-8"
    )

    total = len(profiles) * len(scenes)
    print(f"gallery: {len(present)}/{total} shots, {len(scenes)} scenes -> {out_dir}")
    missing = [
        f"{p['id']}__{s['id']}"
        for p in profiles
        for s in scenes
        if (p["id"], s["id"]) not in present
    ]
    if missing:
        print("missing shots:", ", ".join(missing))


if __name__ == "__main__":
    main()
