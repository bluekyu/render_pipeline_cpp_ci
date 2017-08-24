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
__TARGET_LIST = ["panda3d-thirdparty", "panda3d", "render_pipeline_cpp", "rpcpp_plugins",
                 "rpcpp_samples", "all"]
__target = None
__install_path = None
__cache_path = None
__artifacts_path = None
__cmake_generator = None


def print_debug(msg):
    print("\x1b[32;1m", msg, "\x1b[0m", sep="", flush=True)


def print_error(msg):
    print("\x1b[31;1m", msg, "\x1b[0m", sep="", flush=True)


def build_project(target, git_url, branch="master", ignore_cache=False, artifacts_url=None,
                  install_prefix=None, cmake_args=[]):
    print_debug("-" * 79)
    print_debug("Project: {}".format(git_url))

    git_repo = project_utils.GitProject(git_url, branch)
    if (__target != target) and not ignore_cache:
        if artifacts_url:
            print_debug("-- get latest build")
            project_utils.download_and_extract_archive(artifacts_url, __install_path / target)
            return False

        if __cache_path:
            git_repo.set_hash_file_path(__cache_path / (git_repo.name + ".hash"))

            repo_cache_hash = git_repo.get_cache_hash()
            repo_hash = git_repo.get_hash() if git_repo.exists() else git_repo.get_remote_hash()

            if repo_hash == repo_cache_hash:
                print_debug("-- cache is up to date")
                return False
            else:
                print_debug("-- repository was updated to {} from {}".format(repo_hash, repo_cache_hash))

            git_repo.remove_hash_file()

    if not git_repo.exists():
        print_debug("-- setup git")
        git_repo.clone()

    # setup cmake
    print_debug("-- setup cmake")
    if not install_prefix:
        install_prefix = __install_path / git_repo.name

    project = project_utils.CMakeProject(target, install_prefix=install_prefix.absolute())
    project.remove_install()

    print_debug("---- source directory: {}".format(project.source_dir))
    print_debug("---- binary directory: {}".format(project.binary_dir))
    project.generate(__cmake_generator, cmake_args)
    project.install()

    if __target == target:
        project.install_prefix = __artifacts_path
        project.generate(__cmake_generator)
        project.install()
        print_debug("-- artifacts are created")
    elif __cache_path:
        if git_repo.create_hash_file():
            print_debug("-- hash file is created")
        else:
            print_error("-- Failed to create hash file")
    return True


def main(args):
    # debug cache diretory
    if __cache_path and __cache_path.exists():
        print_debug("-- listing cache directory")
        for cache_files in __cache_path.iterdir():
            print_debug(str(cache_files))

    did_build = False

    # panda3d-thirdparty ######################################################
    if __target == __TARGET_LIST[0]:
        did_build = True

    did_build = build_project(
        target=__TARGET_LIST[0],
        git_url="https://github.com/bluekyu/panda3d-thirdparty.git",
        branch="develop",
        ignore_cache=did_build,
        artifacts_url="https://ci.appveyor.com/api/projects/bluekyu/panda3d-thirdparty/artifacts/panda3d-thirdparty.zip?branch=develop",
        cmake_args=["-Dbuild_minimal:BOOL=ON"])

    os.environ["MAKEPANDA_THIRDPARTY"] = (__install_path / "panda3d-thirdparty").as_posix()

    if not args.all and (__target == __TARGET_LIST[0]):
        return

    # panda3d #################################################################
    if __target == __TARGET_LIST[1]:
        did_build = True

    did_build = build_project(
        target=__TARGET_LIST[1],
        git_url="https://github.com/bluekyu/panda3d.git",
        branch="develop",
        ignore_cache=did_build,
        cmake_args=["-Dpanda3d_build_minimal:BOOL=ON"])

    # reduce the size of cache
    for pdb_path in (__install_path / "panda3d" / "bin").glob("*.pdb"):
        os.remove(pdb_path.as_posix())
    import_libs = [f.stem for f in (__install_path / "panda3d" / "lib").glob("*.exp")]
    for lib_path in (__install_path / "panda3d" / "lib").glob("*.lib"):
        if lib_path.stem not in import_libs:
            os.remove(lib_path.as_posix())

    panda3d_ROOT_posix = (__install_path / "panda3d").as_posix()

    if not args.all and (__target == __TARGET_LIST[1]):
        return

    # YAML-CPP ################################################################
    did_build = build_project(
        "yaml-cpp",
        git_url="https://github.com/jbeder/yaml-cpp.git",
        branch="master",
        ignore_cache=False) or did_build

    # spdlog ##################################################################
    did_build = build_project(
        "spdlog",
        git_url="https://github.com/gabime/spdlog.git",
        branch="v0.13.0",
        ignore_cache=False) or did_build

    # flatbuffers #############################################################
    did_build = build_project(
        "flatbuffers",
        git_url="https://github.com/google/flatbuffers.git",
        branch="v1.7.1",
        ignore_cache=False) or did_build

    # render_pipeline_cpp #####################################################
    if not args.all and (__target == __TARGET_LIST[2]):
        did_build = True

    did_build = build_project(
        __TARGET_LIST[2],
        git_url="https://github.com/bluekyu/render_pipeline_cpp.git",
        branch="master",
        cmake_args=["-DBoost_USE_STATIC_LIBS:BOOL=ON",
                    "-DBOOST_ROOT:PATH={}".format(BOOST_ROOT) if BOOST_ROOT else "",
                    "-Dpanda3d_ROOT:PATH={}".format(panda3d_ROOT_posix),
                    "-Dyaml-cpp_DIR:PATH={}".format((__install_path / "yaml-cpp" / "CMake").as_posix()),
                    "-DFlatBuffers_ROOT:PATH={}".format((__install_path / "flatbuffers").as_posix())],
        ignore_cache=did_build)

    if not args.all and (__target == __TARGET_LIST[2]):
        return

    # rpcpp_plugins ###########################################################
    if __target == __TARGET_LIST[3]:
        did_build = True

    did_build = build_project(
        __TARGET_LIST[3],
        git_url="https://github.com/bluekyu/rpcpp_plugins.git",
        branch="master",
        cmake_args=["-DBoost_USE_STATIC_LIBS:BOOL=ON",
                    "-DBOOST_ROOT:PATH={}".format(BOOST_ROOT) if BOOST_ROOT else "",
                    "-Dpanda3d_ROOT:PATH={}".format(panda3d_ROOT_posix),
                    "-Drpcpp_plugins_BUILD_background2d:BOOL=ON"],
        ignore_cache=did_build)

    if not args.all and (__target == __TARGET_LIST[3]):
        return

    # rpcpp_samples ###########################################################
    if __target == __TARGET_LIST[4]:
        did_build = True

    did_build = build_project(
        __TARGET_LIST[4],
        git_url="https://github.com/bluekyu/rpcpp_samples.git",
        branch="master",
        cmake_args=["-DBoost_USE_STATIC_LIBS:BOOL=ON",
                    "-DBOOST_ROOT:PATH={}".format(BOOST_ROOT) if BOOST_ROOT else "",
                    "-Dpanda3d_ROOT:PATH={}".format(panda3d_ROOT_posix),
                    "-Drpcpp_samples_BUILD_panda3d_samples:BOOL=ON",
                    "-Drpcpp_samples_BUILD_render_pipeline_samples:BOOL=ON"],
        ignore_cache=did_build)

    if not args.all and (__target == __TARGET_LIST[4]):
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=__TARGET_LIST, type=str, help="Set a 'TARGET' to rebuild always "
                        "and build until the TARGET if '--all' option does not set")
    parser.add_argument("--cmake-generator", type=str, required=True, help="Set cmake generator. "
                        "ex) \"Visual Studio 15 2017 Win64\"")
    parser.add_argument("--install-prefix", type=str, required=True, help="Set directory path used for cmake install prefix")
    parser.add_argument("--cache-prefix", type=str, help="Set directory path used for cache")
    parser.add_argument("--artifacts-prefix", type=str, help="Generate artifacts directory for the 'TARGET'")
    parser.add_argument("--all", action="store_true", help="Build including targets after given 'TARGET'")
    args = parser.parse_args()

    __target = args.target
    __install_path = pathlib.Path(args.install_prefix).absolute()
    if args.cache_prefix:
        __cache_path = pathlib.Path(args.cache_prefix).absolute()
    if args.artifacts_prefix:
        __artifacts_path = pathlib.Path(args.artifacts_prefix).absolute()
    __cmake_generator = args.cmake_generator

    main(args)

    def scan_directory_size(directory):
        total_size = 0
        with os.scandir(directory) as it:
            for f in it:
                if f.is_dir():
                    total_size += scan_directory_size(f.path)
                elif f.is_file():
                    total_size += os.path.getsize(f.path)
        return total_size

    # artifacts size
    if __artifacts_path and __artifacts_path.exists():
        print_debug("Artifacts size: {:.3f} MiB".format(scan_directory_size(__artifacts_path) / 1024 / 1024))

    # cache size
    if __cache_path and __cache_path.exists():
        print_debug("Cache size: {:.3f} MiB".format(scan_directory_size(__cache_path) / 1024 / 1024))
