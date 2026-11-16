Name:       llvm-tools-subpkgs
Summary:    Debugging/analysis tool subpackages for the Tizen LLVM toolchain
Version:    22.1.8
Release:    1
License:    NCSA
Group:      Development/Tools
Source0:    llvm-22.1.8.tar.gz
BuildRequires: cmake
BuildRequires: ninja
BuildRequires: llvm
BuildRequires: llvm-devel
# llvm-static-devel: llvm-devel's LLVMExports.cmake validates the static
# imported targets (libLLVM*.a) at configure time; without the archives
# present, find_package(LLVM) aborts before bolt can link the dylib.
BuildRequires: llvm-static-devel
# libomp: the exported target "omp" in LLVMExports-release.cmake references
# /usr/lib64/libomp.so; the configure-time existence check aborts without it.
BuildRequires: libomp
# zlib-devel, libxml2-devel: the exported LLVM targets reference ZLIB::ZLIB
# and LibXml2::LibXml2 in their link interfaces (bolt standalone build)
BuildRequires: zlib-devel
BuildRequires: libxml2-devel
BuildRequires: clang
BuildRequires: libllvm
BuildRequires: compiler-rt

%description
Standalone subpackages for LLVM debugging and analysis tools:
 - bolt: BOLT post-link binary optimizer, built standalone against the
   installed LLVM toolchain (no full LLVM rebuild required)

The tools below (scan-build, llvm-xray, llvm-cov, llvm-profgen, llvm-profdata,
and the analyzer libexec scripts) now ship from the llvm and clang packages,
because llvm-devel's exports and the clang-analyzer files need them there.
Changes to this spec only require
rebuilding this package (minutes), not the multi-hour LLVM build.

%package -n bolt
Summary: BOLT post-link binary optimizer
License: NCSA
Requires: libllvm
Requires: compiler-rt

%description -n bolt
BOLT is a post-link binary optimizer that reorders code in the final
binary or DSO based on runtime profile data (perf LBR/PT samples) to
improve instruction cache and TLB utilization.

%prep
%setup -q -n llvm-22.1.8

# MANDATORY under gbs: gbs builds with _build_create_debug 1, so Tizen's
# patched rpmbuild injects the debuginfo/debugsource package sections
# itself; the standard debug_package macro would add them a second time
# and fail with "package already exists". NOTE: keep percent signs out of
# this comment -- rpmbuild expands macros even in comment lines.
# Debuginfo IS still generated (find-debuginfo.sh runs in
# __os_install_post): bolt-debuginfo and the debugsource package are
# produced. The -Wl,--build-id=sha1 linker flags above make the bolt
# binaries debug-correlatable.
%define debug_package %{nil}

%build
# ---- A. BOLT built standalone against the installed toolchain ----
# Standalone detection: CMAKE_SOURCE_DIR == bolt source dir
# => BOLT_BUILT_STANDALONE=TRUE, find_package(LLVM) finds /usr/lib64/cmake/llvm.
# LLVM_LINK_LLVM_DYLIB=ON is mandatory: Tizen ships libLLVM.so (libllvm) and
# only STATIC IMPORTED targets in llvm-devel; the static component archives
# live in llvm-static-devel which is not installed here.
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
    -DLLVM_LIBDIR_SUFFIX=64 \
    -DLLVM_ENABLE_RTTI=ON \
    -DLLVM_LINK_LLVM_DYLIB=ON \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--build-id=sha1" \
    -DCMAKE_SHARED_LINKER_FLAGS="-Wl,--build-id=sha1" \
    -DBOLT_INCLUDE_TESTS=OFF \
%ifarch armv7l
    -DBOLT_ENABLE_RUNTIME=OFF \
%endif
    -DLLVM_INCLUDE_TESTS=OFF
# bolt: driver + tools; bolt_rt: runtime archives (ExternalProject).
# CMake enables the runtime only on x86_64/aarch64/riscv64 hosts, so armv7l
# builds just the driver. The runtime is for instrumenting x86/aarch64 targets.
%ifarch armv7l
ninja bolt
%else
ninja bolt bolt_rt
%endif

%install
# ---- A. bolt: install from the standalone build tree ----
cd bolt-build
DESTDIR=%{buildroot} ninja install
# The internal bolt static libs are build artifacts, not shipped content.
rm -f %{buildroot}%{_libdir}/libLLVMBOLT*.a
# LLVM_LIBDIR_SUFFIX=64 installs the internal archives to lib64 instead.
rm -f %{buildroot}%{_prefix}/lib64/libLLVMBOLT*.a
# perf2bolt and llvm-boltdiff are aliases of llvm-bolt: upstream installs them
# as symlinks (bolt/tools/driver/CMakeLists.txt), and llvm-bolt selects its
# mode from the name it is invoked as. Separate copies also collided on
# build-id in the debuginfo step.
ln -sf llvm-bolt %{buildroot}%{_prefix}/bin/perf2bolt
ln -sf llvm-bolt %{buildroot}%{_prefix}/bin/llvm-boltdiff
# llvm-bat-dump and merge-fdata use add_bolt_executable which carries no
# install rule; stage them manually from the build tree.
install -p -m 0755 bin/llvm-bat-dump %{buildroot}%{_prefix}/bin/
install -p -m 0755 bin/merge-fdata   %{buildroot}%{_prefix}/bin/
cd ..

%files -n bolt
%defattr(-,root,root,-)
%{_prefix}/bin/llvm-bolt
%{_prefix}/bin/perf2bolt
%{_prefix}/bin/llvm-boltdiff
%{_prefix}/bin/llvm-bolt-heatmap
%{_prefix}/bin/llvm-bolt-binary-analysis
%{_prefix}/bin/llvm-bat-dump
%{_prefix}/bin/merge-fdata
%ifnarch armv7l
%{_libdir}/libbolt_rt_instr.a
%{_libdir}/libbolt_rt_hugify.a
%endif

