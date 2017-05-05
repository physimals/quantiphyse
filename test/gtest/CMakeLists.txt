cmake_minimum_required(VERSION 2.8)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

#set(gtest_SOURCE_DIR lib/googletest/googletest)
add_subdirectory(googletest-release-1.7.0)

message("gtest_SOURCE_DIR: ${gtest_SOURCE_DIR}")
include_directories(${gtest_SOURCE_DIR}/include ${gtest_SOURCE_DIR})

add_executable(runT10Tests basic_check.cpp)

target_link_libraries(runT10Tests gtest gtest_main)
target_link_libraries(runT10Tests T10lib fsliolib)
target_link_libraries(runT10Tests ${NIFTI_LIBRARIES})
target_link_libraries(runT10Tests ${OpenCV_LIBS})
