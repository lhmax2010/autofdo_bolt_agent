#!/bin/sh


  RPM_SOURCE_DIR="/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/SOURCES"
  RPM_BUILD_DIR="/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD"
  RPM_OPT_FLAGS="-Os -ffunction-sections -fdata-sections -fstack-protector -Wno-unused-command-line-argument -Wno-error=unused-but-set-variable -Wno-error=unused-command-line-argument -momit-leaf-frame-pointer  -g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -Wformat -Wformat-security -fmessage-length=0 -frecord-gcc-switches -fdiagnostics-color=never -m64 -march=nehalem -msse4.2 -mfpmath=sse -fasynchronous-unwind-tables -fno-omit-frame-pointer -g"
  RPM_ARCH="x86_64"
  RPM_OS="linux"
  export RPM_SOURCE_DIR RPM_BUILD_DIR RPM_OPT_FLAGS RPM_ARCH RPM_OS
  RPM_DOC_DIR="%{_docdir}"
  export RPM_DOC_DIR
  RPM_PACKAGE_NAME="llvm-tools-subpkgs"
  RPM_PACKAGE_VERSION="22.1.8"
  RPM_PACKAGE_RELEASE="1"
  export RPM_PACKAGE_NAME RPM_PACKAGE_VERSION RPM_PACKAGE_RELEASE
  LANG=C
  export LANG
  unset CDPATH DISPLAY ||:
  RPM_BUILD_ROOT="/home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64"
  export RPM_BUILD_ROOT
  
  PKG_CONFIG_PATH="${PKG_CONFIG_PATH}:/usr/lib64/pkgconfig:/usr/share/pkgconfig"
  export PKG_CONFIG_PATH
  
  exec > /dev/null
  umask 022
  cd "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD"

  CFLAGS="${CFLAGS:--Os -ffunction-sections -fdata-sections -fstack-protector -Wno-unused-command-line-argument -Wno-error=unused-but-set-variable -Wno-error=unused-command-line-argument -momit-leaf-frame-pointer  -g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -Wformat -Wformat-security -fmessage-length=0 -frecord-gcc-switches -fdiagnostics-color=never -m64 -march=nehalem -msse4.2 -mfpmath=sse -fasynchronous-unwind-tables -fno-omit-frame-pointer -g}" ; export CFLAGS ; 
  CXXFLAGS="${CXXFLAGS:--Os -ffunction-sections -fdata-sections -fstack-protector -Wno-unused-command-line-argument -Wno-error=unused-but-set-variable -Wno-error=unused-command-line-argument -momit-leaf-frame-pointer  -g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -Wformat -Wformat-security -fmessage-length=0 -frecord-gcc-switches -fdiagnostics-color=never -m64 -march=nehalem -msse4.2 -mfpmath=sse -fasynchronous-unwind-tables -fno-omit-frame-pointer -g}" ; export CXXFLAGS ; 
  LDFLAGS="${LDFLAGS:--Wl,-z,relro,--as-needed -Wl,--gc-sections}" ; export LDFLAGS;

ninja() { command /usr/bin/ninja -j2 "$@"; }; export CMAKE_BUILD_PARALLEL_LEVEL=2



cd 'llvm-22.1.8'
export AR=llvm-ar RANLIB=llvm-ranlib;
export CC=x86_64-tizen-linux-gnu-clang CXX=x86_64-tizen-linux-gnu-clang++;
export MAKEFLAGS+=" -k";

# ---- A. BOLT built standalone against the installed toolchain ----
# Standalone detection: CMAKE_SOURCE_DIR == bolt source dir
# => BOLT_BUILT_STANDALONE=TRUE, find_package(LLVM) finds the installed
# LLVM CMake package under the architecture libdir.
# LLVM_LINK_LLVM_DYLIB=ON is mandatory: BOLT must link libLLVM.so (libllvm);
# llvm-static-devel is installed only because the exported targets are
# validated at configure time.
#
# All LLVM provider packages must come from one LLVM build.
test "$(llvm-config --version)" = "22.1.8" || exit 1
llvm_evr=""
for p in llvm llvm-devel llvm-static-devel libllvm libomp; do
    e=$(rpm -q --qf '%{VERSION}-%{RELEASE}' "$p") || exit 1
    if [ -n "$llvm_evr" ] && [ "$e" != "$llvm_evr" ]; then
        echo "LLVM provider mismatch: $p $e, expected $llvm_evr"
        exit 1
    fi
    llvm_evr=$e
done
echo "BOLT is built against LLVM provider $llvm_evr"
mkdir -p bolt-build
cd bolt-build
cmake \
    -G Ninja \
    -S ../bolt \
    -B . \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_CXX_COMPILER=clang++ \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DLLVM_LIBDIR_SUFFIX=`echo lib64 | sed s/lib//g` \
    -DLLVM_ENABLE_RTTI=ON \
    -DLLVM_LINK_LLVM_DYLIB=ON \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--build-id=sha1" \
    -DCMAKE_SHARED_LINKER_FLAGS="-Wl,--build-id=sha1" \
    -DBOLT_INCLUDE_TESTS=OFF \
    -DBOLT_TARGETS_TO_BUILD="X86;AArch64" \
    -DLLVM_INCLUDE_TESTS=OFF
# bolt: driver + tools; bolt_rt: runtime archives (ExternalProject) for the
# build architecture.
ninja bolt bolt_rt
# Target registration check, kept in the build section so it also runs
# when the check section is skipped. It does not test a rewrite.
LC_ALL=C ./bin/llvm-bolt --version > bolt-version.txt 2>&1 || { cat bolt-version.txt; exit 1; }
cat bolt-version.txt
grep -Eq '^[[:space:]]*aarch64[[:space:]]+-' bolt-version.txt
grep -Eq '^[[:space:]]*x86-64[[:space:]]+-' bolt-version.txt



exit $?

