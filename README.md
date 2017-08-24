# Continuous Integration for Render Pipeline C++

[![Windows build status](https://ci.appveyor.com/api/projects/status/efs56usknquscufm/branch/master?svg=true)](https://ci.appveyor.com/project/bluekyu/render-pipeline-cpp-ci/branch/master)

This project is for continuous integration to build
[Render Pipeline C++](https://github.com/bluekyu/render_pipeline_cpp) project.


## Build
```
python build.py TARGET --cmake-generator "Visual Studio 15 2017 Win64" --install-prefix="C:/projects/_install"
```
`TARGET` is one of `panda3d-thirdparty`, `panda3d`, `render_pipeline_cpp`, `rpcpp_plugins`, `rpcpp_samples`, `all`.
Build of the target will be re-build.


## Pipeline
`build.py` script is just a batch of commands using Python:
```
for project in ALL_PROJECTS:
    check build dependency;
    build_project()

def build_project():
    check build cache;
    setup git;
    build cmake && install to cache;
```


## Related Projects
- Panda3D Third-party: https://github.com/bluekyu/panda3d-thirdparty
- (patched) Panda3D: https://github.com/bluekyu/panda3d
- Render Pipeline C++: https://github.com/bluekyu/render_pipeline_cpp
- Plugins for Render Pipeline C++: https://github.com/bluekyu/rpcpp_plugins
- Samples for Render Pipeline C++: https://github.com/bluekyu/rpcpp_samples
