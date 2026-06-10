"""Wipe <sketch_dir>/output/ before each capture test so the sketch starts
from a clean directory and the test asserts on freshly produced PNGs.

DO NOT copy this hook elsewhere without auditing: `shutil.rmtree` removes any
directory literally named `output` sitting next to a pytest test module. Here
the only such directory is screenshot/output, which is generated content
(see .gitignore).

各キャプチャテストの前に <sketch_dir>/output/ を消し、スケッチが常にクリーンな
状態から PNG を書き出すようにする。`output` という名前のディレクトリを無条件で
削除するため、他リポジトリへ流用する際は要注意。
"""

import shutil
from pathlib import Path


def pytest_runtest_setup(item):
    output_dir = Path(item.fspath).parent / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
