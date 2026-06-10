"""Headless capture of every profile x scene to output/<profile>__<scene>.png.

Drives the screenshot sketch on the lang-ship:host mode=lgfx backend (SDL dummy)
and asserts that a non-empty PNG was produced for each shot.

全プロファイル x 全シーンを output/<profile>__<scene>.png にキャプチャし、
各ショットが空でない PNG として書き出されたことを検証する。
"""

from pathlib import Path

SKETCH_DIR = Path(__file__).resolve().parent


def test_screenshot(dut):
    dut.expect("TEST start screenshot", timeout=60)
    dut.expect("TEST done", timeout=180)

    out = SKETCH_DIR / "output"
    pngs = sorted(out.glob("*.png"))
    assert pngs, f"no PNGs produced in {out}"
    for p in pngs:
        assert p.stat().st_size > 100, f"empty/short PNG: {p}"
