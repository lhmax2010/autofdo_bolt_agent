Name:           afdo-spike
Version:        1.0
Release:        1
Summary:        Deterministic AutoFDO and instrumentation PGO feasibility test
License:        MIT
Source0:        %{name}-%{version}.tar.gz
BuildRequires:  llvm
BuildRequires:  compiler-rt
BuildRequires:  glibc-devel
BuildRequires:  binutils
ExclusiveArch:  aarch64

# Keep the exact profiled ELF, full symbols, DWARF and link relocations.
%global debug_package %{nil}
%global __debug_install_post %{nil}
%global __os_install_post %{nil}
%global __strip /bin/true

%description
A small integer workload for checking profile generation and profile use.
No Agent implementation and no RPM installation on the development board.

%prep
%setup -q

%build
set -eux
clang --version
llvm-profdata --version
common='-O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names -Wl,--build-id=sha1 -Wl,--emit-relocs'
clang $common spike.c -o afdo-spike-base
clang $common -fprofile-generate spike.c -o afdo-spike-instr
%if 0%{?with_pgo}
# The committed profile is portable text; binary profile remains in the buildroot.
llvm-profdata merge instr.proftext -o instr.profdata
clang $common -fprofile-use=instr.profdata -Werror=profile-instr-out-of-date -Werror=profile-instr-unprofiled -Rpass=pgo-instrumentation -Rpass-missed=pgo -fsave-optimization-record -fdiagnostics-show-hotness spike.c -o afdo-spike-pgo
# Persist IR evidence that the matched profile set entry counts and branch weights.
clang -O2 -gline-tables-only -fdebug-info-for-profiling -funique-internal-linkage-names -fprofile-use=instr.profdata -Werror=profile-instr-out-of-date -Werror=profile-instr-unprofiled -S -emit-llvm spike.c -o afdo-spike-pgo.ll
%endif
%if 0%{?with_afdo}
clang $common -fprofile-sample-use=afdo.extbinary -Rpass=sample-profile -Rpass-missed=sample-profile spike.c -o afdo-spike-afdo
%endif
# These are the platform tools inside the GBS build environment.
for exe in afdo-spike-base afdo-spike-instr %{?with_pgo:afdo-spike-pgo} %{?with_afdo:afdo-spike-afdo}; do
    readelf -h "$exe"
    readelf -SW "$exe"
    readelf -n "$exe"
done

%install
mkdir -p %{buildroot}%{_bindir}
install -m 0755 afdo-spike-base afdo-spike-instr %{buildroot}%{_bindir}/
%if 0%{?with_pgo}
install -m 0755 afdo-spike-pgo %{buildroot}%{_bindir}/
%endif
%if 0%{?with_afdo}
install -m 0755 afdo-spike-afdo %{buildroot}%{_bindir}/
%endif

%files
%{_bindir}/afdo-spike-base
%{_bindir}/afdo-spike-instr
%if 0%{?with_pgo}
%{_bindir}/afdo-spike-pgo
%endif
%if 0%{?with_afdo}
%{_bindir}/afdo-spike-afdo
%endif
