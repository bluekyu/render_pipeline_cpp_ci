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
import project_utils


# custom settings
BOOST_ROOT = ""

# internal variables
__TARGET_LIST = ["panda3d-thirdparty", "panda3d", "render_pipeline_cpp", "all"]


def print_debug(msg):
    print("\x1b[32;1m", msg, "\x1b[0m", sep="", flush=True)


def print_error(msg):
    print("\x1b[31;1m", msg, "\x1b[0m", sep="", flush=True)


def build_project(git_url, cmake_generator, install_path, branch="master", cmake_args=[], ignore_cache=False):
    print_debug("-" * 79)
    print_debug("Project: {}".format(git_url))

    install_path = pathlib.Path(install_path).absolute()

    git_repo = project_utils.GitProject(git_url, branch)
    git_repo.set_hash_file_path(install_path / (git_repo.name + ".hash"))

    if not ignore_cache:
        repo_cache_hash = git_repo.get_cache_hash()
        repo_hash = git_repo.get_hash() if git_repo.exists() else git_repo.get_remote_hash()

        if repo_hash == repo_cache_hash:
            print_debug("-- cache is up to date")
            return False
        else:
            print_debug("-- repository was updated to {} from {}".format(repo_hash, repo_cache_hash))

    git_repo.remove_hash_file()

    if not git_repo.exists():
        print_debug("-- start git")
        git_repo.clone()

    print_debug("-- start cmake")
    project = project_utils.CMakeProject(git_repo.name, install_prefix=(install_path / git_repo.name))
    project.remove_install()

    print_debug("---- source directory: {}".format(project.source_dir))
    print_debug("---- binary directory: {}".format(project.binary_dir))
    project.generate(cmake_generator, cmake_args)
    project.install()

    if git_repo.create_hash_file():
        print_debug("-- hash file is created")
    else:
        print_error("-- Failed to create hash file")
    return True


def main(args):
    install_path = pathlib.Path(args.install_prefix).absolute()

    # debug cache diretory
    if install_path.exists():
        print_debug("-- Listring install directory")
        for cache_files in install_path.iterdir():
            print_debug(str(cache_files))

    did_build = False

    # panda3d-thirdparty
    if args.target == __TARGET_LIST[1]:
        did_build = True

    did_build = build_project(
        git_url="https://github.com/bluekyu/panda3d-thirdparty.git",
        branch="develop",
        install_path=install_path,
        cmake_generator=args.cmake_generator,
        cmake_args=["-Dbuild_minimal:BOOL=ON"],
        ignore_cache=did_build)

    os.environ["MAKEPANDA_THIRDPARTY"] = (install_path / "panda3d-thirdparty").as_posix()

    if args.target == __TARGET_LIST[0]:
        return

    # panda3d
    if args.target == __TARGET_LIST[1]:
        did_build = True

    did_build = build_project(
        git_url="https://github.com/bluekyu/panda3d.git",
        branch="develop",
        cmake_generator=args.cmake_generator,
        install_path=install_path,
        cmake_args=["-Dpanda3d_build_minimal:BOOL=ON"],
        ignore_cache=did_build)

    # reduce the size of cache
    for pdb_path in (install_path / "panda3d" / "bin").glob("*.pdb"):
        os.remove(pdb_path.as_posix())
    import_libs = [f.stem for f in (install_path / "panda3d" / "lib").glob("*.exp")]
    for lib_path in (install_path / "panda3d" / "lib").glob("*.lib"):
        if lib_path.stem not in import_libs:
            os.remove(lib_path.as_posix())

    if args.target == __TARGET_LIST[1]:
        return

    # YAML-CPP
    did_build = build_project(
        git_url="https://github.com/jbeder/yaml-cpp.git",
        branch="yaml-cpp-0.5.3",
        cmake_generator=args.cmake_generator,
        install_path=install_path,
        cmake_args=["-DBOOST_ROOT:PATH={}".format(BOOST_ROOT) if BOOST_ROOT else ""],
        ignore_cache=False) or did_build

    # spdlog
    did_build = build_project(
        git_url="https://github.com/gabime/spdlog.git",
        branch="v0.13.0",
        cmake_generator=args.cmake_generator,
        install_path=install_path,
        ignore_cache=False) or did_build

    # flatbuffers
    did_build = build_project(
        git_url="https://github.com/google/flatbuffers.git",
        branch="v1.7.1",
        cmake_generator=args.cmake_generator,
        install_path=install_path,
        ignore_cache=False) or did_build

    # render_pipeline_cpp
    if args.target == __TARGET_LIST[2]:
        did_build = True

    if args.target == __TARGET_LIST[2]:
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=__TARGET_LIST, type=str)
    parser.add_argument("--cmake-generator", type=str, required=True)
    parser.add_argument("--install-prefix", type=str, required=True)
    args = parser.parse_args()

    main(args)

    # cache size
    def scan_directory_size(directory):
        total_size = 0
        with os.scandir(directory) as it:
            for f in it:
                if f.is_dir():
                    total_size += scan_directory_size(f.path)
                elif f.is_file():
                    total_size += os.path.getsize(f.path)
        return total_size

    print_debug("Cache size: {:.3f} MiB".format(
        scan_directory_size(pathlib.Path(args.install_prefix)) / 1024 / 1024))
