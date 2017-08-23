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


class GitProject:
    git_cmd = "git"

    def __init__(self, url, branch="master"):
        self.url = url
        self.branch = branch
        self.name = re.search("^.*/(.*?)\.git$", self.url).group(1)

    def set_hash_file_path(self, hash_file_path):
        self.hash_file_path = pathlib.Path(hash_file_path)

    def ls_remote(self):
        result = subprocess.run([self.git_cmd, "ls-remote", "--heads", "--tags", self.url],
                                stdout=subprocess.PIPE, check=True).stdout.decode()
        result = result.strip("\n")
        result = result.split("\n")
        ref_dict = {}
        for s in result:
            sha1, refs = s.split("\t")
            match = re.match("^refs/(\\w+?)/(.+)$", refs)
            ref_dict.setdefault(match.group(1), {})[match.group(2)] = sha1
        return ref_dict

    def get_remote_hash(self, point=None):
        if not point:
            point = self.branch

        ref_dict = self.ls_remote()
        if point in ref_dict["heads"]:
            return ref_dict["heads"][point]
        elif (point+"^{}") in ref_dict["tags"]:
            # first, dereference the tag
            return ref_dict["tags"][point+"^{}"]
        elif point in ref_dict["tags"]:
            return ref_dict["tags"][point]
        return None

    def get_hash(self, point="HEAD"):
        self.exists(True)
        return subprocess.run([self.git_cmd, "rev-parse", point],
                              stdout=subprocess.PIPE, cwd=self.name, check=True).stdout.decode()

    def create_hash_file(self):
        with self.hash_file_path.open("w") as hash_file:
            hash_file.write(self.get_hash())
            return True
        return False

    def remove_hash_file(self):
        if self.hash_file_path.exists():
            os.remove(self.hash_file_path.as_posix())

    def get_cache_hash(self):
        if self.hash_file_path.exists():
            with self.hash_file_path.open() as hash_file:
                return hash_file.readline().strip()
        return None

    def clone(self, point=None):
        if not point:
            point = self.branch
        subprocess.run([self.git_cmd, "clone", "--branch", point, self.url], check=True)

    def exists(self, strict=False):
        if (pathlib.Path(self.name) / ".git").exists():
            return True
        if strict:
            raise RuntimeError("Git directory does NOT exist.")
        return False


class CMakeProject:
    cmake_cmd = "cmake"

    def __init__(self, source_dir, install_prefix, config="Release", binary_dir="_build"):
        self.config = config

        source_dir = pathlib.Path(source_dir).absolute()
        self.source_dir = source_dir.as_posix()
        self.binary_dir = (pathlib.Path(binary_dir).absolute() / source_dir.name).as_posix()
        self.install_prefix = pathlib.Path(install_prefix).absolute().as_posix()

    def generate(self, cmake_generator, additional_args=[]):
        binary_dir_path = pathlib.Path(self.binary_dir)
        if not binary_dir_path.exists():
            binary_dir_path.mkdir(parents=True)
        subprocess.run([self.cmake_cmd, "-G", cmake_generator,
                        "-DCMAKE_INSTALL_PREFIX="+self.install_prefix,
                        *additional_args,
                        self.source_dir],
                       cwd=self.binary_dir,
                       check=True)

    def build(self):
        subprocess.run([self.cmake_cmd, "--build", ".", "--config", self.config,
                        "--target", "ALL_BUILD"],
                       cwd=self.binary_dir,
                       check=True)

    def install(self):
        subprocess.run([self.cmake_cmd, "--build", ".", "--config", self.config,
                        "--target", "INSTALL"],
                       cwd=self.binary_dir,
                       check=True)

    def remove_install(self):
        if pathlib.Path(self.install_prefix).exists():
            shutil.rmtree(self.install_prefix)
