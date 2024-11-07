#!/usr/bin/env python3

import subprocess
from pathlib import Path

root_tests_dir = Path(__file__).parent.resolve()
prog = "g++"

for test_dir in root_tests_dir.iterdir():
    if test_dir.is_dir():
        print(test_dir)
        a_dir = test_dir / "a"
        b_dir = test_dir / "b"

        a_dir.mkdir(exist_ok=True)
        b_dir.mkdir(exist_ok=True)

        test_files = list(test_dir.glob('*.c??'))
        subprocess.run([prog, "-DV1", "-o", a_dir/"program.out", "-g", *test_files], check=True)
        subprocess.run([prog, "-DV2", "-o", b_dir/"program.out", "-g", *test_files], check=True)
