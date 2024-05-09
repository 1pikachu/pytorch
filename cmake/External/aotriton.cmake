if(NOT __AOTRITON_INCLUDED)
  set(__AOTRITON_INCLUDED TRUE)

  set(__AOTRITON_SOURCE_DIR "${CMAKE_CURRENT_BINARY_DIR}/aotriton/src")
  set(__AOTRITON_BUILD_DIR "${CMAKE_CURRENT_BINARY_DIR}/aotriton/build")
  set(__AOTRITON_INSTALL_DIR "${PROJECT_SOURCE_DIR}/torch")
  ExternalProject_Add(aotriton_external
    GIT_REPOSITORY https://github.com/ROCm/aotriton.git
    GIT_TAG a42c19d59dabb7c47606b6dc12168b3fff104e24
    SOURCE_DIR ${__AOTRITON_SOURCE_DIR}
    BINARY_DIR ${__AOTRITON_BUILD_DIR}
    PREFIX ${__AOTRITON_INSTALL_DIR}
    CMAKE_ARGS -DCMAKE_INSTALL_PREFIX:PATH=${__AOTRITON_INSTALL_DIR}
    -DAOTRITON_COMPRESS_KERNEL=OFF
    -DCMAKE_BUILD_TYPE=${CMAKE_BUILD_TYPE}
    -DAOTRITON_NO_PYTHON=ON
    -DAOTRITON_NO_SHARED=ON
    # CONFIGURE_COMMAND ""
    BUILD_COMMAND ""  # Install command will do the installation for us
    BUILD_BYPRODUCTS "${__AOTRITON_INSTALL_DIR}/lib/libaotriton_v2.a"
    USES_TERMINAL_DOWNLOAD TRUE
    USES_TERMINAL_CONFIGURE TRUE
    USES_TERMINAL_BUILD TRUE
    USES_TERMINAL_INSTALL TRUE
    # INSTALL_COMMAND ${MAKE_COMMAND} install
    )
  set(AOTRITON_FOUND TRUE)
  add_library(__caffe2_aotriton INTERFACE)
  add_dependencies(__caffe2_aotriton aotriton_external)
  target_link_libraries(__caffe2_aotriton INTERFACE ${__AOTRITON_INSTALL_DIR}/lib/libaotriton_v2.a)
  target_include_directories(__caffe2_aotriton INTERFACE ${__AOTRITON_INSTALL_DIR}/include)
endif() # __AOTRITON_INCLUDED
