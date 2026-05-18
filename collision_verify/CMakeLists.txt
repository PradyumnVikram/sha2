cmake_minimum_required(VERSION 3.16)
project(collision_verify LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(collision_verify
    src/main.cpp
)

target_include_directories(collision_verify PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_options(collision_verify PRIVATE
    $<$<CXX_COMPILER_ID:GNU,Clang>:-Wall -Wextra -Wpedantic>
)
