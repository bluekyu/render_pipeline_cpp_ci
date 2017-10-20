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

cmake_minimum_required(VERSION 3.4)

find_package(PythonInterp REQUIRED)
find_package(Git REQUIRED)

file(DOWNLOAD
    "https://raw.githubusercontent.com/bluekyu/render_pipeline_cpp_ci/master/builder.py"
    "${CMAKE_CURRENT_SOURCE_DIR}/builder.py"
    STATUS download_status
    TIMEOUT 30
)
list(GET download_status 0 download_status)

if(NOT (${download_status} EQUAL 0))
    message(FATAL_ERROR "Failed to download builder.py")
endif()

get_filename_component(builder_install_prefix
    ${builder_install_prefix}
    ABSOLUTE
)

execute_process(COMMAND ${PYTHON_EXECUTABLE} builder.py
    "${builder_url}"
    --branch "${builder_branch}"
    --cmake-generator "${builder_cmake_generator}"
    --install-prefix "${builder_install_prefix}"

    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    ENCODING AUTO
)
