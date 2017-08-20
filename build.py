"""
MIT License

Copyright (c) 2017 Younguk Kim

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


import pathlib
import subprocess
import argparse
import sys
import os
from project_utils import *


GIT_EXE = "git"
CMAKE_EXE = "cmake"
TARGET_LIST = ["panda3d-thirdparty", "panda3d", "all"]


def print_debug(msg):
    print("\x1b[32;1m", msg, "\x1b[0m", sep="", flush=True)


def build_project(git_url, cmake_generator, branch="master", cmake_args=[], ignore_cache=False):
    print_debug("-" * 79)
    print_debug("Project: {}".format(git_url))

    git_repo = GitProject(git_url, branch)

    if (not ignore_cache) and git_repo.check_cache():
        print_debug("-- cache is used")
        return False
    else:
        git_repo.remove_hash_file()
        if not git_repo.exists():
            print_debug("-- start git")
            git_repo.clone()

        print_debug("-- start cmake")
        project = CMakeProject(git_repo.name)
        project.remove_install()

        project.generate(cmake_generator, cmake_args)
        project.install()

        git_repo.create_hash_file()
        print_debug("-- hash file is created")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=TARGET_LIST, type=str)
    parser.add_argument("--cmake-generator", type=str, required=True)

    args = parser.parse_args()

    subprocess.run([GIT_EXE, "--version"], check=True)
    subprocess.run([CMAKE_EXE, "--version"], check=True)

    did_build = True

    # panda3d-thirdparty
    did_build = did_build and not (args.target == TARGET_LIST[0])
    did_build = build_project(
        git_url="https://github.com/bluekyu/panda3d-thirdparty.git",
        branch="develop",
        cmake_generator=args.cmake_generator,
        cmake_args=["-Dbuild_minimal:BOOL=ON"],
        ignore_cache=(not did_build))
    os.environ["MAKEPANDA_THIRDPARTY"] = (pathlib.Path(INSTALLED_DIR).resolve() / "panda3d-thirdparty").as_posix()

    if args.target == TARGET_LIST[0]:
        sys.exit(0)

    # panda3d
    if args.target == TARGET_LIST[1]:
        did_build = False

    did_build = build_project(
        git_url="https://github.com/bluekyu/panda3d.git",
        branch="develop",
        cmake_generator=args.cmake_generator,
        cmake_args=["-Dpanda3d_build_minimal:BOOL=ON"],
        ignore_cache=(not did_build))

    if args.target == TARGET_LIST[1]:
        sys.exit(0)
