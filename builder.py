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
import argparse
import os
import shlex
import subprocess
import re
import shutil
import urllib.request
import uuid
import zipfile


def print_debug(msg):
    print("\x1b[32;1m", msg, "\x1b[0m", sep="", flush=True)


def print_error(msg):
    print("\x1b[31;1m", msg, "\x1b[0m", sep="", flush=True)


class GitProject:
    git_cmd = "git"

    def __init__(self, url, branch="master", commit=None):
        self.url = url
        if commit:
            self.commit = commit
        elif branch:
            self.branch = branch
        else:
            self.branch = "master"

        self.name = re.search("^.*/(.*?)\.git$", self.url).group(1)

    @property
    def branch(self):
        return self._branch

    @branch.setter
    def branch(self, branch):
        self._branch = branch
        self._commit = None

    @property
    def commit(self):
        return self._commit

    @commit.setter
    def commit(self, commit):
        self._branch = None
        self._commit = commit

    @property
    def hash_file_path(self):
        return self._hash_file_path

    @hash_file_path.setter
    def hash_file_path(self, hash_file_path):
        self._hash_file_path = pathlib.Path(hash_file_path)

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
                              stdout=subprocess.PIPE, cwd=pathlib.Path(self.name), check=True).stdout.decode()

    def create_hash_file(self):
        with self.hash_file_path.open("w") as hash_file:
            hash_file.write(self.get_hash())
            return True
        return False

    def remove_hash_file(self):
        if self.hash_file_path.exists():
            os.remove(self.hash_file_path)

    def read_cache_hash(self):
        if self.hash_file_path.exists():
            with self.hash_file_path.open() as hash_file:
                return hash_file.readline().strip()
        return None

    def is_cached(self):
        cache_hash = self.read_cache_hash()
        if not cache_hash:
            return False

        if self.commit:
            if self.commit == cache_hash[:len(self.commit)]:
                return True
            return False

        repo_hash = self.get_hash() if self.exists() else self.get_remote_hash()
        if repo_hash == cache_hash:
            return True
        return False

    def clone(self, depth=None):
        cmd = [self.git_cmd, "clone"]
        if self.branch:
            cmd += ["--branch", self.branch]
            if depth:
                cmd += ["--depth", str(depth)]
            cmd += [self.url]
            subprocess.run(cmd, check=True)
        elif self.commit:
            cmd += ["--no-checkout", self.url]
            subprocess.run(cmd, check=True)

        if self.commit:
            self.checkout(self.commit)

    def checkout(self, point=None):
        subprocess.run([self.git_cmd, "checkout", point], cwd=pathlib.Path(self.name), check=True)

    def exists(self, strict=False):
        if (pathlib.Path(self.name) / ".git").exists():
            return True
        if strict:
            raise RuntimeError("Git directory does NOT exist.")
        return False


class CMakeProject:
    cmake_cmd = "cmake"

    def __init__(self, source_dir, install_prefix, config, binary_dir="build"):
        self.config = config

        source_dir = pathlib.Path(source_dir).absolute()
        self.source_dir = source_dir.as_posix()
        self.binary_dir = (source_dir / binary_dir).as_posix()
        self.install_prefix = install_prefix

    @property
    def install_prefix(self):
        return self._install_prefix

    @install_prefix.setter
    def install_prefix(self, path):
        self._install_prefix = pathlib.Path(path).absolute().as_posix()

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


def download_and_extract_archive(url, dest_path=None):
    response = urllib.request.urlopen(url)
    if not response:
        return False
    tmp_file_path = pathlib.Path(str(uuid.uuid4()) + ".zip").absolute()
    with tmp_file_path.open("wb") as tmp_file:
        tmp_file.write(response.read())

    if not dest_path:
        dest_path = pathlib.Path.cwd()
    dest_path = pathlib.Path(dest_path).absolute().as_posix()

    zipfile.ZipFile(tmp_file_path.as_posix()).extractall(dest_path)

    os.remove(tmp_file_path)


def main(args):
    install_prefix = pathlib.Path(args.install_prefix).absolute()
    hash_path = None
    if args.hash_path:
        hash_path = pathlib.Path(args.hash_path).absolute()

    print_debug("-" * 79)
    print_debug("Project: {}".format(args.git_url))

    git_repo = GitProject(args.git_url, branch=args.branch, commit=args.commit)
    if hash_path:
        git_repo.hash_file_path = hash_path
        if git_repo.is_cached():
            print_debug("-- cache is up to date")
            return
        print_debug("-- cache is invalid")

    if not git_repo.exists():
        print_debug("-- setup git")
        git_repo.clone(depth=1)

    # setup cmake
    print_debug("-- setup cmake")

    project = CMakeProject(git_repo.name, install_prefix, args.config)
    project.remove_install()

    print_debug("---- source directory: {}".format(project.source_dir))
    print_debug("---- binary directory: {}".format(project.binary_dir))
    project.generate(args.cmake_generator, shlex.split(args.cmake_args) if args.cmake_args else [])
    project.install()

    if hash_path:
        if git_repo.create_hash_file():
            print_debug("-- hash file is created")
        else:
            print_error("-- failed to create hash file")

    def scan_directory_size(directory):
        total_size = 0
        with os.scandir(directory) as it:
            for f in it:
                if f.is_dir():
                    total_size += scan_directory_size(f.path)
                elif f.is_file():
                    total_size += os.path.getsize(f.path)
        return total_size

    # cache size
    if hash_path and hash_path.exists():
        print_debug("Cache size: {:.3f} MiB".format(scan_directory_size(install_prefix) / 1024 / 1024))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("git_url", type=str, help="Git URL of target project.")

    git_tag_group = parser.add_mutually_exclusive_group()
    git_tag_group.add_argument("--branch", type=str, default="master", help="Branch of target project.")
    git_tag_group.add_argument("--commit", type=str, help="Commit of target project.")

    parser.add_argument("--config", type=str, default="Release", help="Set cmake configuration.")
    parser.add_argument("--cmake-generator", type=str, required=True, help="Set cmake generator. "
                        "ex) \"Visual Studio 15 2017 Win64\"")
    parser.add_argument("--install-prefix", type=str, required=True, help="Set directory path used for cmake install prefix")
    parser.add_argument("--cmake-args", type=str, help="Set extra arguments in CMake.")
    parser.add_argument("--hash-path", type=str, help="Set path of hash file")

    main(parser.parse_args())
