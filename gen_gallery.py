#!/usr/bin/env python3
"""Generate the screenshot gallery (Python stdlib only -- no Node, no deps).

Reads the PNGs captured by screenshot/test_screenshot.py and the project file
(*.lgfxsb.json, for profile/scene order + scene descriptions), copies the
images under docs/shots/<profile>/<scene>.png, and emits two static pages:

  docs/index.html      "By profile"  -- every scene for each profile
  docs/by-scene.html   "By scene"    -- every profile side-by-side per scene

キャプチャ済み PNG とプロジェクトファイル（順序・シーン説明の取得用）から、
画像を docs/shots/ 配下へ配置し、プロファイル単位／シーン単位の 2 ページを
生成する。Python 標準ライブラリのみで動作（Node・外部依存なし）。

Usage:
    python3 gen_gallery.py [--project Sfm.lgfxsb.json]
                           [--shots screenshot/output] [--out docs]
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent


def find_project(explicit: str | None) -> Path:
    if explicit:
        return (REPO_ROOT / explicit).resolve()
    matches = sorted(REPO_ROOT.glob("*.lgfxsb.json"))
    if not matches:
        raise SystemExit("no *.lgfxsb.json found in repo root")
    return matches[0]


def load_model(project_path: Path):
    data = json.loads(project_path.read_text(encoding="utf-8"))
    name = data.get("name") or project_path.stem
    profiles = [
        {
            "id": p["id"],
            "w": int(p["w"]),
            "h": int(p["h"]),
            "rotation": int(p.get("rotation", 0)),
        }
        for p in data.get("profiles", [])
    ]
    scenes = [
        {"id": s["id"], "desc": (s.get("desc") or "").strip()}
        for s in data.get("scenes", [])
    ]
    return name, profiles, scenes


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
  display: flex; justify-content: space-between; gap: 12px;
}
figcaption .dim { color: #6b7780; }
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
}})();
</script>
</body>
</html>
"""


def img_tag(rel_src: str, prof) -> str:
    # Native size carried via --w; display size = --w * --zoom (header dropdown).
    # width/height attrs are the native px so layout is stable before CSS loads.
    return (
        f'<img src="{rel_src}" alt="" style="--w:{prof["w"]}" '
        f'width="{prof["w"]}" height="{prof["h"]}" loading="lazy">'
    )


def render_by_profile(profiles, scenes, present, project, generated) -> str:
    out = []
    for prof in profiles:
        rot = f" / rot {prof['rotation'] * 90}°" if prof["rotation"] else ""
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
                + f'<figcaption><span>{html.escape(scene["id"])}</span></figcaption>'
                + "</figure>"
            )
        out.append("</div></section>")
    if not present:
        out.append('<p class="empty">No screenshots found. Run the capture first.</p>')
    return page(f"{project} screenshots", project, generated, "profile", "\n".join(out))


def render_by_scene(profiles, scenes, present, project, generated) -> str:
    out = []
    for scene in scenes:
        out.append('<section class="group">')
        out.append(f"<h2>{html.escape(scene['id'])}</h2>")
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
    ap.add_argument("--project", default=None, help="path to *.lgfxsb.json")
    ap.add_argument("--shots", default="screenshot/output", help="captured PNG dir")
    ap.add_argument("--out", default="docs", help="output gallery dir")
    args = ap.parse_args()

    project_path = find_project(args.project)
    shots_dir = (REPO_ROOT / args.shots).resolve()
    out_dir = (REPO_ROOT / args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    name, profiles, scenes = load_model(project_path)
    present = collect_shots(shots_dir, out_dir, profiles, scenes)
    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    (out_dir / "index.html").write_text(
        render_by_profile(profiles, scenes, present, name, generated), encoding="utf-8"
    )
    (out_dir / "by-scene.html").write_text(
        render_by_scene(profiles, scenes, present, name, generated), encoding="utf-8"
    )

    total = len(profiles) * len(scenes)
    print(f"gallery: {len(present)}/{total} shots -> {out_dir}")
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
