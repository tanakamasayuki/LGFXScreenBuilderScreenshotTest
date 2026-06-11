"""Wipe <sketch_dir>/output/ before the *capture* test so the sketch starts
from a clean directory and the test asserts on freshly produced PNGs. The
gallery test reuses those PNGs, so it must NOT trigger the wipe -- we gate on
the `dut` fixture, which only the capture test requests.

(gen_gallery now lives next to the tests in screenshot/, so `import gen_gallery`
resolves via pytest's normal test-dir sys.path -- no manual insert needed.)

DO NOT copy this hook elsewhere without auditing: `shutil.rmtree` removes any
directory literally named `output` sitting next to a pytest test module. Here
the only such directory is screenshot/output, which is generated content
(see .gitignore).

キャプチャテストの前だけ output/ を消す。ギャラリーテストはその PNG を再利用する
ため、`dut` フィクスチャを使うテスト（=キャプチャ）に限定して削除する。
"""

import shutil
from pathlib import Path


def pytest_runtest_setup(item):
    # Only the capture test requests `dut`; the gallery test reuses its output.
    if "dut" not in item.fixturenames:
        return
    output_dir = Path(item.fspath).parent / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
