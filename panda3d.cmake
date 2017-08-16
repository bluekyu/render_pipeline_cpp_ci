# https://github.com/bluekyu/panda3d
option(panda3d_ENABLE_CI "Enable CI for the project." ON)
if(panda3d_ENABLE_CI)
    option(panda3d_MANUAL_GIT "Manage the git project manually." OFF)
    set(panda3d_SOURCE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/panda3d"
        CACHE PATH "SOURCE_DIR of the project")
    set(panda3d_BINARY_DIR "${CMAKE_CURRENT_BINARY_DIR}/_build_panda3d")

    set(panda3d_PATCH_COMMAND "")
    if(WIN32 AND panda3d_thirdparty_ENABLE_CI)
        set(panda3d_THIRDPARTY_DIR "win-libs-vc")
        if(MSVC_VERSION LESS 1600)
            message(FATAL_ERROR "Unknown Visual Studio.")
        elseif(MSVC_VERSION LESS 1700)  # vs2010
            set(panda3d_THIRDPARTY_DIR "${panda3d_THIRDPARTY_DIR}10")
        elseif(MSVC_VERSION LESS 1800)  # vs2012
            set(panda3d_THIRDPARTY_DIR "${panda3d_THIRDPARTY_DIR}11")
        elseif(MSVC_VERSION LESS 1900)  # vs2013
            set(panda3d_THIRDPARTY_DIR "${panda3d_THIRDPARTY_DIR}12")
        elseif(MSVC_VERSION LESS_EQUAL 1911)  # vs2015 and vs2017
            set(panda3d_THIRDPARTY_DIR "${panda3d_THIRDPARTY_DIR}14")
        else()
            message(FATAL_ERROR "Unknown Visual Studio.")
        endif()

        if(CMAKE_GENERATOR MATCHES "Win64$")
            set(panda3d_THIRDPARTY_DIR "${panda3d_THIRDPARTY_DIR}-x64")
        endif()
        set(panda3d_THIRDPARTY_DIR_PATH "${panda3d_SOURCE_DIR}/thirdparty/${panda3d_THIRDPARTY_DIR}")

        string(REPLACE "/" "\\" panda3d_THIRDPARTY_LINK_WIN_PATH "${panda3d_THIRDPARTY_DIR_PATH}")
        string(REPLACE "/" "\\" panda3d_THIRDPARTY_TARGET_WIN_PATH
            "${panda3d_thirdparty_SOURCE_DIR}/${panda3d_THIRDPARTY_DIR}")

        set(panda3d_PATCH_COMMAND if not exist ${panda3d_THIRDPARTY_LINK_WIN_PATH}
            mklink /J ${panda3d_THIRDPARTY_LINK_WIN_PATH}
            ${panda3d_THIRDPARTY_TARGET_WIN_PATH})
    endif()

    if(panda3d_MANUAL_GIT)
        ExternalProject_Add(panda3d_git
            DEPENDS panda3d_thirdparty_git

            PATCH_COMMAND ${CMAKE_COMMAND} -E make_directory "${panda3d_SOURCE_DIR}/thirdparty"
                  COMMAND ${panda3d_PATCH_COMMAND}
            SOURCE_DIR ${panda3d_SOURCE_DIR}
            CMAKE_CACHE_ARGS -Dpanda3d_build_minimal:BOOL=ON

            BINARY_DIR ${panda3d_BINARY_DIR}
            INSTALL_COMMAND ""
        )
    else()
        ExternalProject_Add(panda3d_git
            DEPENDS panda3d_thirdparty_git
            GIT_REPOSITORY https://github.com/bluekyu/panda3d.git
            GIT_TAG develop
            GIT_PROGRESS 1

            PATCH_COMMAND ${CMAKE_COMMAND} -E make_directory "${panda3d_SOURCE_DIR}/thirdparty"
                  COMMAND ${panda3d_PATCH_COMMAND}
            SOURCE_DIR ${panda3d_SOURCE_DIR}
            CMAKE_CACHE_ARGS -Dpanda3d_build_minimal:BOOL=ON

            BINARY_DIR ${panda3d_BINARY_DIR}
            INSTALL_COMMAND ""
        )
    endif()
else()
    add_custom_target(panda3d_thirdparty)
    message("panda3d-thirdparty is disabled.")
endif()
