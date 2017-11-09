#
# For help: cmake --help-command <command>

cmake_minimum_required(VERSION 2.8)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")
project(25_T10_calculation)

find_package(OpenCV)

# Finding nifti libraries
# ========================================================
FIND_PATH(NIFTI_INCLUDE_DIR
        nifti1.h
        /usr/local/include/nifti /usr/include/nifti)
FIND_LIBRARY( NIFTI_BASE_LIBRARY
        NAMES libniftiio${CMAKE_SHARED_LIBRARY_SUFFIX} libniftiio${CMAKE_STATIC_LIBRARY_SUFFIX}
        )

FIND_LIBRARY( NIFTI_ZNZ_LIBRARY
        NAMES libznz${CMAKE_SHARED_LIBRARY_SUFFIX} libznz${CMAKE_STATIC_LIBRARY_SUFFIX}
        )

SET( NIFTI_INCLUDE_DIRS
        ${NIFTI_INCLUDE_DIR}
        ${ZLIB_INCLUDE_DIRS}
        )
SET( NIFTI_LIBRARIES
        ${NIFTI_BASE_LIBRARY}
        ${NIFTI_ZNZ_LIBRARY}
        ${ZLIB_LIBRARIES}
        )

# ========================================================

# adds the testing command add_test
enable_testing()

#header files
include_directories(T10)
include_directories(T10/libs/fslio)
include_directories(${NIFTI_INCLUDE_DIRS})


# Adding directories with CMakeLists.txt files
add_subdirectory(T10)
add_subdirectory(tests)

set(SOURCE_FILES example.cpp)
add_executable(T10calc ${SOURCE_FILES})
# linking library to executalbe
target_link_libraries(T10calc T10lib fsliolib)
target_link_libraries(T10calc ${NIFTI_LIBRARIES})
target_link_libraries(T10calc ${OpenCV_LIBS})

# Add test for CTest. Command line run example:
# cd build
# cmake ../
# cmake --build .
# ctest -VV
add_test(test1 T10_tests/runT10Tests)
