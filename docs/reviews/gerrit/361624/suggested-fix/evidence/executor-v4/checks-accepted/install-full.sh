#!/bin/sh


  RPM_SOURCE_DIR="/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/SOURCES"
  RPM_BUILD_DIR="/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD"
  RPM_OPT_FLAGS="-Os -ffunction-sections -fdata-sections -fstack-protector -Wno-unused-command-line-argument -Wno-error=unused-but-set-variable -Wno-error=unused-command-line-argument -momit-leaf-frame-pointer  -g2 -gdwarf-4 -pipe -Wall -Wp,-D_FORTIFY_SOURCE=2 -fexceptions -Wformat -Wformat-security -fmessage-length=0 -frecord-gcc-switches -fdiagnostics-color=never -m64 -march=nehalem -msse4.2 -mfpmath=sse -fasynchronous-unwind-tables -fno-omit-frame-pointer -g"
  RPM_ARCH="x86_64"
  RPM_OS="linux"
  export RPM_SOURCE_DIR RPM_BUILD_DIR RPM_OPT_FLAGS RPM_ARCH RPM_OS
  RPM_DOC_DIR="/usr/share/doc/packages"
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

/bin/rm -rf "$RPM_BUILD_ROOT"
/bin/mkdir -p "$RPM_BUILD_ROOT"

ninja() { command /usr/bin/ninja -j2 "$@"; }; export CMAKE_BUILD_PARALLEL_LEVEL=2



cd 'llvm-22.1.8'
export AR=llvm-ar RANLIB=llvm-ranlib;
export CC=x86_64-tizen-linux-gnu-clang CXX=x86_64-tizen-linux-gnu-clang++;

# ---- A. bolt: install from the standalone build tree ----
cd bolt-build
DESTDIR=/home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64 ninja install
# The internal bolt static libs are build artifacts, not shipped content.
rm -f /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64/usr/lib64/libLLVMBOLT*.a
# LLVM_LIBDIR_SUFFIX=64 installs the internal archives to lib64 instead.
rm -f /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64/usr/lib64/libLLVMBOLT*.a
# perf2bolt and llvm-boltdiff are aliases of llvm-bolt: upstream installs them
# as symlinks (bolt/tools/driver/CMakeLists.txt), and llvm-bolt selects its
# mode from the name it is invoked as. Separate copies also collided on
# build-id in the debuginfo step.
ln -sf llvm-bolt /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64/usr/bin/perf2bolt
ln -sf llvm-bolt /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64/usr/bin/llvm-boltdiff
# llvm-bat-dump and merge-fdata use add_bolt_executable which carries no
# install rule; stage them manually from the build tree.
install -p -m 0755 bin/llvm-bat-dump /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64/usr/bin/
install -p -m 0755 bin/merge-fdata   /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64/usr/bin/
cd ..



    
    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/find-debuginfo.sh \
    -j2 \
     \
     \
     \
     \
    --build-id-seed "22.1.8-1" \
     \
    --unique-debug-src-base "llvm-tools-subpkgs-22.1.8-1.x86_64" \
     \
     \
     \
     \
    -S debugsourcefiles.list \
    "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8"\
    
   cp /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/debug.manifest /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/llvm-tools-subpkgs-debuginfo.manifest 
   cp /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/debug.manifest /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/llvm-tools-subpkgs-debugsource.manifest 
 

    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/check-buildroot
    
    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm//brp-compress 
    
     
    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/brp-strip-static-archive /bin/strip 
#    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/brp-strip-comment-note /bin/strip /bin/objdump 

    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/brp-python-hardlink 
    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/tizen/find-docs.sh /home/abuild/rpmbuild/BUILDROOT/llvm-tools-subpkgs-22.1.8-1.x86_64 

    
    /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/usr/lib/rpm/tizen/find-isufiles.sh /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/home/abuild/rpmbuild/BUILD/llvm-22.1.8/isu.list 

    
    


