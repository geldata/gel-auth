#
# This source file is part of the Gel open source project.
#
# Copyright 2025-present Gel Data Inc. and the Gel authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import pathlib
import subprocess
import sys
import unittest


def find_root_path() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent


class TestSourceCode(unittest.TestCase):
    def test_cqa_mypy(self) -> None:
        root_path = find_root_path()
        config_path = root_path / "pyproject.toml"
        if not config_path.exists():
            raise RuntimeError("could not locate pyproject.toml file")

        try:
            import mypy  # NoQA
        except ImportError:
            raise unittest.SkipTest("mypy module is missing")

        for subdir in ["src", "tests"]:
            with self.subTest(subdir=subdir):
                try:
                    subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "mypy",
                            "--config-file",
                            config_path,
                            subdir,
                        ],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=root_path,
                    )
                except subprocess.CalledProcessError as ex:
                    output = ex.stdout.decode()
                    if ex.stderr:
                        output += "\n\n" + ex.stderr.decode()
                    raise AssertionError(
                        f"mypy validation failed:\n{output}"
                    ) from None

    def test_cqa_ruff(self):
        root_path = find_root_path()

        try:
            import ruff  # type: ignore  # NoQA
        except ImportError:
            raise unittest.SkipTest("ruff module is missing")

        for subdir in ["src", "tests"]:
            with self.subTest(subdir=subdir):
                try:
                    subprocess.run(
                        ["ruff", "check", subdir],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        cwd=root_path,
                    )
                except subprocess.CalledProcessError as ex:
                    output = ex.output.decode()
                    raise AssertionError(
                        f"ruff validation failed:\n{output}"
                    ) from None
