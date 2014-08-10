cmake_minimum_required(VERSION 2.8)
project(SafeRunner)

set(CMAKE_BUILD_TYPE Release)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O3")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -std=c++11")

find_package(CURL REQUIRED)
find_package(PythonLibs REQUIRED)
find_package(Boost COMPONENTS python REQUIRED)

find_package(PkgConfig REQUIRED)
pkg_check_modules(Sodium REQUIRED libsodium)

include_directories(
    ${Boost_INCLUDE_DIR}
    ${PYTHON_INCLUDE_DIRS}
    ${Sodium_INCLUDE_DIRS}
    ${CURL_INCLUDE_DIR}
)
link_directories(${Sodium_LIBRARY_DIRS})

aux_source_directory(src SafeRunner_files)
add_library(SafeRunner SHARED ${SafeRunner_files})
target_link_libraries(
  SafeRunner
  ${PYTHON_LIBRARY}
  ${CURL_LIBRARY}
  ${Boost_LIBRARIES}
  ${Sodium_LIBRARIES}
  cryptopp
)

set_target_properties(SafeRunner PROPERTIES PREFIX "")
if(WIN32)
  set_target_properties(SafeRunner PROPERTIES SUFFIX ".pyd")
else(WIN32)
  if(UNIX)
    set_target_properties(SafeRunner PROPERTIES SUFFIX ".so")
  endif(UNIX)
endif(WIN32)
