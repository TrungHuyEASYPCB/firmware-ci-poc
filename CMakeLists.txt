cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(firmware_ci_poc)

set(FW_VERSION "0.0.0-dev")

if(DEFINED ENV{FW_VERSION} AND NOT "$ENV{FW_VERSION}" STREQUAL "")
  set(FW_VERSION "$ENV{FW_VERSION}")
elseif(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/RELEASE_VERSION")
  file(READ "${CMAKE_CURRENT_SOURCE_DIR}/RELEASE_VERSION" FW_VERSION)
  string(STRIP "${FW_VERSION}" FW_VERSION)
endif()

execute_process(
  COMMAND git rev-parse --short HEAD
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  OUTPUT_VARIABLE FW_GIT_COMMIT
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_QUIET
)

execute_process(
  COMMAND git rev-parse --abbrev-ref HEAD
  WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
  OUTPUT_VARIABLE FW_GIT_REF
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_QUIET
)

if(NOT FW_GIT_COMMIT)
  set(FW_GIT_COMMIT "unknown")
endif()

if(NOT FW_GIT_REF)
  set(FW_GIT_REF "unknown")
endif()

set(FW_BOARD "$ENV{FW_BOARD}")

if("${FW_BOARD}" STREQUAL "")
  set(FW_BOARD "$ENV{BOARD}")
endif()

if("${FW_BOARD}" STREQUAL "")
  set(FW_BOARD "${BOARD}")
endif()

string(TIMESTAMP FW_BUILD_TIME "%Y-%m-%dT%H:%M:%SZ" UTC)

message(STATUS "Firmware version: ${FW_VERSION}")
message(STATUS "Firmware git commit: ${FW_GIT_COMMIT}")
message(STATUS "Firmware git ref: ${FW_GIT_REF}")
message(STATUS "Firmware board: ${FW_BOARD}")
message(STATUS "Firmware build time: ${FW_BUILD_TIME}")

configure_file(
  ${CMAKE_CURRENT_SOURCE_DIR}/cmake/app_version.h.in
  ${CMAKE_CURRENT_BINARY_DIR}/generated/app_version.h
  @ONLY
)

target_include_directories(app PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/generated)

target_sources(app PRIVATE app/src/main.c)
