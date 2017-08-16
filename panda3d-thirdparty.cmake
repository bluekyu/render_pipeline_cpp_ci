# https://github.com/bluekyu/panda3d-thirdparty
option(panda3d_thirdparty_ENABLE_CI "Enable CI for the project." ON)
if(panda3d_thirdparty_ENABLE_CI)
    option(panda3d_thirdparty_MANUAL_GIT "Manage the git project manually." OFF)
    set(panda3d_thirdparty_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/panda3d-thirdparty"
        CACHE PATH "SOURCE_DIR of the project")
    set(panda3d_thirdparty_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/_build_panda3d-thirdparty")

    if(panda3d_thirdparty_MANUAL_GIT)
        ExternalProject_Add(panda3d_thirdparty_git
            SOURCE_DIR ${panda3d_thirdparty_SOURCE_DIR}
            CMAKE_CACHE_ARGS -Dbuild_minimal:BOOL=ON

            BINARY_DIR ${panda3d_thirdparty_BINARY_DIR}
            INSTALL_COMMAND ""
        )
    else()
        ExternalProject_Add(panda3d_thirdparty_git
            GIT_REPOSITORY https://github.com/bluekyu/panda3d-thirdparty.git
            GIT_TAG develop
            GIT_PROGRESS 1

            SOURCE_DIR ${panda3d_thirdparty_SOURCE_DIR}
            CMAKE_CACHE_ARGS -Dbuild_minimal:BOOL=ON

            BINARY_DIR ${panda3d_thirdparty_BINARY_DIR}
            INSTALL_COMMAND ""
        )
    endif()
else()
    add_custom_target(panda3d_thirdparty)
    message("panda3d-thirdparty is disabled.")
endif()
