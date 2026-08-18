# Builds the Pico SDK's Doxygen docs and nothing else.
#
# Requires doxygen and a host compiler. It deliberately does not need arm-none-eabi-gcc:
# see cmake/pico_docs_toolchain.cmake for why that works.
#
#   cmake -S . -B build -DPICO_SDK_PATH=pico-sdk -DPICO_PLATFORM=rp2040
#   cmake --build build --target docs
#
# The docs land in build/pico-sdk/docs/doxygen/html.

cmake_minimum_required(VERSION 3.13)

# Before project(), which is when CMake reads it.
set(CMAKE_TOOLCHAIN_FILE "${CMAKE_CURRENT_LIST_DIR}/cmake/pico_docs_toolchain.cmake"
        CACHE FILEPATH "Host toolchain, so the SDK does not reach for arm-none-eabi")

project(picodocs C CXX ASM)

if (NOT PICO_SDK_PATH)
    message(FATAL_ERROR "Set PICO_SDK_PATH to a pico-sdk checkout")
endif()
get_filename_component(PICO_SDK_PATH "${PICO_SDK_PATH}" REALPATH BASE_DIR "${CMAKE_CURRENT_LIST_DIR}")

# On, since the SDK only defaults it on for its own top-level build. PICO_SDK_TESTS_ENABLED
# is left off by the same rule, which is a saving here rather than a loss.
set(PICO_BUILD_DOCS 1 CACHE BOOL "" FORCE)

add_subdirectory("${PICO_SDK_PATH}" pico-sdk)

if (NOT TARGET docs)
    message(FATAL_ERROR "The SDK did not offer a docs target")
endif()
