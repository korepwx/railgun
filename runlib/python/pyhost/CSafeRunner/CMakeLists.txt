cmake_minimum_required(VERSION 2.8)
project(SafeRunner)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O3")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -std=c++11")

# CURL, python-dev, boost-python
find_package(CURL REQUIRED)
find_package(PythonLibs REQUIRED)
find_package(Boost COMPONENTS python REQUIRED)

include_directories(
    ${Boost_INCLUDE_DIR}
    ${PYTHON_INCLUDE_DIRS}
    ${CURL_INCLUDE_DIR}
)

# find cryptopp
find_path(CRYPTOPP_INCLUDE_DIR
  cryptopp/cryptlib.h
  PATHS
    /opt/local/include
    /usr/local/include
    /usr/include
)
find_library(CRYPTOPP_LIBRARY
  NAMES cryptopp
  PATHS
    /opt/local/lib
    /usr/local/lib
    /usr/lib
)
include_directories(${CRYPTOPP_INCLUDE_DIR})

# gather source files
aux_source_directory(src SafeRunner_files)

# add build target
add_executable(SafeRunner ${SafeRunner_files})
target_link_libraries(
  SafeRunner
  ${PYTHON_LIBRARY}
  ${CURL_LIBRARY}
  ${Boost_LIBRARIES}
  ${CRYPTOPP_LIBRARY}
)
