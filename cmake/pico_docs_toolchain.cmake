# An empty toolchain file to trick the docs into building without 3GB of toolchain.
#
# The SDK's top-level CMakeLists calls project(pico_sdk C CXX ASM) at line 10 and reaches
# add_subdirectory(docs) at the end of the same file, so some toolchain has to answer
# before Doxygen is ever considered. pico_pre_load_toolchain only picks arm-none-eabi when
# CMAKE_TOOLCHAIN_FILE is unset. This empty toolchain leaves the host compiler in place.
#
# Nothing is built for the target: `--target docs` runs Doxygen over the headers and
# compiles no source files. The generated Doxyfile and all 1086 HTML files come out
# byte-identical to an arm-none-eabi build.
