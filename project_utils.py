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


import subprocess
import re
import pathlib
import shutil
import os


GIT_EXE = "git"
CMAKE_EXE = "cmake"
BUILD_DIR = "_build"
INSTALLED_DIR = "_install"


class GitProject:
    def __init__(self, url, branch="master"):
        self.url = url
        self.branch = branch
        self.name = re.search("^.*/(.*?)\.git$", self.url).group(1)
        self.hash_file_path = pathlib.Path(INSTALLED_DIR) / (self.name + ".hash")

    def get_remote_hash(self):
        try:
            return self.__hash
        except AttributeError:
            result = subprocess.run([GIT_EXE, "ls-remote", self.url, self.branch],
                                    stdout=subprocess.PIPE, check=True).stdout.decode()
            match = re.search("^([0-9a-f]{40})\t", result)
            self.__hash = match.group(1)
            return self.__hash

    def get_hash(self):
        return subprocess.run([GIT_EXE, "rev-parse", "HEAD"],
                              stdout=subprocess.PIPE, cwd=self.name, check=True).stdout.decode()

    def create_hash_file(self):
        with self.hash_file_path.open("w") as hash_file:
            hash_file.write(self.get_hash())

    def remove_hash_file(self):
        if self.hash_file_path.exists():
            os.remove(self.hash_file_path.as_posix())

    def check_cache(self):
        if self.hash_file_path.exists():
            with self.hash_file_path.open() as hash_file:
                cache_hash = hash_file.readline().strip()
                latest_hash = self.get_remote_hash()
                if cache_hash == latest_hash:
                    return True
        return False

    def clone(self):
        subprocess.run([GIT_EXE, "clone", "--branch", self.branch, self.url], check=True)


class CMakeProject:
    def __init__(self, project_dir, config="Release"):
        self.config = config

        self.source_dir = pathlib.Path(project_dir).resolve().as_posix()
        self.binary_dir = (pathlib.Path.cwd() / BUILD_DIR / project_dir).as_posix()
        self.install_prefix = (pathlib.Path.cwd() / INSTALLED_DIR / project_dir).as_posix()

    def generate(self, cmake_generator, additional_args=[]):
        binary_dir_path = pathlib.Path(self.binary_dir)
        if not binary_dir_path.exists():
            binary_dir_path.mkdir(parents=True)
        subprocess.run([CMAKE_EXE, "-G", cmake_generator,
                        "-DCMAKE_INSTALL_PREFIX="+self.install_prefix,
                        *additional_args,
                        self.source_dir],
                       cwd=self.binary_dir,
                       check=True)

    def build(self):
        subprocess.run([CMAKE_EXE, "--build", ".", "--config", self.config,
                        "--target", "ALL_BUILD"],
                       cwd=self.binary_dir,
                       check=True)

    def install(self):
        subprocess.run([CMAKE_EXE, "--build", ".", "--config", self.config,
                        "--target", "INSTALL"],
                       cwd=self.binary_dir,
                       check=True)

    def remove_install(self):
        if pathlib.Path(self.install_prefix).exists():
            shutil.rmtree(self.install_prefix)
