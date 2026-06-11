"""Headless capture of every profile x scene, then build + verify the gallery.

`test_capture` drives the screenshot sketch on the lang-ship:host mode=lgfx
backend (SDL dummy) and asserts a non-empty PNG was produced for each shot.
`test_gallery` then builds docs/ in-process via gen_gallery and asserts every
profile x scene made it in -- so `uv run pytest screenshot/` is the single,
cross-platform entry point (no separate `python3 gen_gallery.py`).

NOTE: order matters. pytest runs tests in definition order within a module, so
`test_capture` (produces output/) must stay above `test_gallery` (consumes it).

全プロファイル x 全シーンをキャプチャし、続けて docs/ ギャラリーを生成・検証する。
gen_gallery を別プロセスで叩かず in-process で呼ぶため `uv run pytest screenshot/`
の 1 コマンドで完結し、Windows でも動く。定義順に実行されるため capture を先に置く。
"""

import json
import re
from pathlib import Path

import gen_gallery

SKETCH_DIR = Path(__file__).resolve().parent


def test_capture(dut):
    dut.expect("TEST start screenshot", timeout=60)
    dut.expect("TEST done", timeout=180)

    out = SKETCH_DIR / "output"
    pngs = sorted(out.glob("*.png"))
    assert pngs, f"no PNGs produced in {out}"
    for p in pngs:
        assert p.stat().st_size > 100, f"empty/short PNG: {p}"


def test_gallery():
    res = gen_gallery.build_gallery()

    # Every profile x scene must be present -- a missing shot is a real failure.
    assert res.present > 0, "gallery built with zero shots; did capture run?"
    assert res.missing == [], f"gallery missing shots: {', '.join(res.missing)}"

    # Each emitted page exists and is non-empty.
    for page in res.pages:
        assert page.exists(), f"gallery page not written: {page}"
        assert page.stat().st_size > 0, f"gallery page is empty: {page}"

    # ai-layouts.js must carry a valid JSON payload keyed by scene id.
    ai_js = (res.out_dir / "ai-layouts.js").read_text(encoding="utf-8")
    m = re.search(r"window\.AI_LAYOUTS = (.*);\n?$", ai_js, re.S)
    assert m, "ai-layouts.js is not in the expected `window.AI_LAYOUTS = {...};` form"
    layouts = json.loads(m.group(1))
    scene_ids = {s["id"] for s in res.scenes}
    assert set(layouts) == scene_ids, "ai-layouts.js scenes != header scenes"
