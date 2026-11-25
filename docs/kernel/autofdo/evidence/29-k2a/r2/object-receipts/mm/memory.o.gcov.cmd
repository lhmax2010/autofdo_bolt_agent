savedcmd_mm/memory.o := clang -fintegrated-cc1 -Wp,-MMD,mm/.memory.o.d -nostdinc -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include -I./arch/arm/include/generated -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include -I./include -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi -I./arch/arm/include/generated/uapi -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi -I./include/generated/uapi -include /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler-version.h -include /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kconfig.h -include /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler_types.h -D__KERNEL__ --target=arm-linux-gnueabi -fintegrated-as -Werror=unknown-warning-option -Werror=ignored-optimization-argument -Werror=option-ignored -Werror=unused-command-line-argument -mlittle-endian -D__LINUX_ARM_ARCH__=7 -fmacro-prefix-map=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/= -std=gnu11 -fshort-wchar -funsigned-char -fno-common -fno-PIE -fno-strict-aliasing -fno-dwarf2-cfi-asm -mtp=cp15 -mabi=aapcs-linux -mfpu=vfp -funwind-tables -meabi gnu -Wa,-W -march=armv7-a -msoft-float -Uarm -fno-delete-null-pointer-checks -O2 -fstack-protector-strong -ftrivial-auto-var-init=zero -pg -fstrict-flex-arrays=3 -fno-strict-overflow -fno-stack-check -fno-builtin-wcslen -fno-builtin-wcslen -Wall -Wextra -Wundef -Werror=implicit-function-declaration -Werror=implicit-int -Werror=return-type -Werror=strict-prototypes -Wno-format-security -Wno-trigraphs -Wno-frame-address -Wno-address-of-packed-member -Wmissing-declarations -Wmissing-prototypes -Wframe-larger-than=1024 -Wno-gnu -Wno-format-overflow-non-kprintf -Wno-format-truncation-non-kprintf -Wno-default-const-init-unsafe -Wvla -Wno-pointer-sign -Wcast-function-type -Wno-unterminated-string-initialization -Wimplicit-fallthrough -Werror=date-time -Werror=incompatible-pointer-types -Wenum-conversion -Wunused -Wno-unused-but-set-variable -Wno-unused-const-variable -Wno-format-overflow -Wno-override-init -Wno-pointer-to-enum-cast -Wno-tautological-constant-out-of-range-compare -Wno-unaligned-access -Wno-enum-compare-conditional -Wno-missing-field-initializers -Wno-type-limits -Wno-shift-negative-value -Wno-enum-enum-conversion -Wno-sign-compare -Wno-unused-parameter -g -gdwarf-4  -fprofile-arcs -ftest-coverage  -fdebug-info-for-profiling -mllvm -enable-fs-discriminator=true -mllvm -improved-fs-discriminator=true -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/mm -Imm    -DKBUILD_MODFILE='"mm/memory"' -DKBUILD_BASENAME='"memory"' -DKBUILD_MODNAME='"memory"' -D__KBUILD_MODNAME=kmod_memory -c -o mm/memory.o /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/mm/memory.c  

source_mm/memory.o := /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/mm/memory.c

deps_mm/memory.o := \
    $(wildcard include/config/COMPILE_TEST) \
    $(wildcard include/config/NUMA) \
    $(wildcard include/config/COMPAT_BRK) \
    $(wildcard include/config/MMU) \
    $(wildcard include/config/ARCH_HAS_PTE_SPECIAL) \
    $(wildcard include/config/PGTABLE_HAS_HUGE_LEAVES) \
    $(wildcard include/config/SMP) \
    $(wildcard include/config/PREEMPTION) \
    $(wildcard include/config/KSM) \
    $(wildcard include/config/TRANSPARENT_HUGEPAGE) \
    $(wildcard include/config/DEBUG_FS) \
    $(wildcard include/config/NUMA_BALANCING) \
    $(wildcard include/config/HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD) \
    $(wildcard include/config/LRU_GEN) \
    $(wildcard include/config/PER_VMA_LOCK) \
    $(wildcard include/config/LOCK_MM_AND_FIND_VMA) \
    $(wildcard include/config/LOCKDEP) \
    $(wildcard include/config/HAVE_IOREMAP_PROT) \
    $(wildcard include/config/PROVE_LOCKING) \
    $(wildcard include/config/DEBUG_ATOMIC_SLEEP) \
    $(wildcard include/config/HUGETLBFS) \
    $(wildcard include/config/SPLIT_PTE_PTLOCKS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler-version.h \
    $(wildcard include/config/CC_VERSION_TEXT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kconfig.h \
    $(wildcard include/config/CPU_BIG_ENDIAN) \
    $(wildcard include/config/BOOGER) \
    $(wildcard include/config/FOO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler_types.h \
    $(wildcard include/config/DEBUG_INFO_BTF) \
    $(wildcard include/config/PAHOLE_HAS_BTF_TAG) \
    $(wildcard include/config/FUNCTION_ALIGNMENT) \
    $(wildcard include/config/CC_HAS_SANE_FUNCTION_ALIGNMENT) \
    $(wildcard include/config/X86_64) \
    $(wildcard include/config/ARM64) \
    $(wildcard include/config/LD_DEAD_CODE_DATA_ELIMINATION) \
    $(wildcard include/config/LTO_CLANG) \
    $(wildcard include/config/HAVE_ARCH_COMPILER_H) \
    $(wildcard include/config/KCSAN) \
    $(wildcard include/config/CC_HAS_COUNTED_BY) \
    $(wildcard include/config/UBSAN_SIGNED_WRAP) \
    $(wildcard include/config/CC_HAS_ASM_INLINE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler_attributes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler-clang.h \
    $(wildcard include/config/ARCH_USE_BUILTIN_BSWAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kernel_stat.h \
    $(wildcard include/config/SCHED_CORE) \
    $(wildcard include/config/GENERIC_IRQ_STAT_SNAPSHOT) \
    $(wildcard include/config/VIRT_CPU_ACCOUNTING_GEN) \
    $(wildcard include/config/VIRT_CPU_ACCOUNTING_NATIVE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/smp.h \
    $(wildcard include/config/UP_LATE_INIT) \
    $(wildcard include/config/DEBUG_PREEMPT) \
    $(wildcard include/config/CSD_LOCK_WAIT_DEBUG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/errno.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/errno.h \
  arch/arm/include/generated/uapi/asm/errno.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/errno.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/errno-base.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/types.h \
    $(wildcard include/config/HAVE_UID16) \
    $(wildcard include/config/UID16) \
    $(wildcard include/config/ARCH_DMA_ADDR_T_64BIT) \
    $(wildcard include/config/PHYS_ADDR_T_64BIT) \
    $(wildcard include/config/64BIT) \
    $(wildcard include/config/ARCH_32BIT_USTAT_F_TINODE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/int-ll64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/int-ll64.h \
  arch/arm/include/generated/uapi/asm/bitsperlong.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitsperlong.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/bitsperlong.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/posix_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stddef.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/stddef.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/posix_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/posix_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/list.h \
    $(wildcard include/config/LIST_HARDENED) \
    $(wildcard include/config/DEBUG_LIST) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/container_of.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/build_bug.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler.h \
    $(wildcard include/config/TRACE_BRANCH_PROFILING) \
    $(wildcard include/config/PROFILE_ALL_BRANCHES) \
    $(wildcard include/config/OBJTOOL) \
  arch/arm/include/generated/asm/rwonce.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/rwonce.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kasan-checks.h \
    $(wildcard include/config/KASAN_GENERIC) \
    $(wildcard include/config/KASAN_SW_TAGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kcsan-checks.h \
    $(wildcard include/config/KCSAN_WEAK_MEMORY) \
    $(wildcard include/config/KCSAN_IGNORE_ATOMICS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/poison.h \
    $(wildcard include/config/ILLEGAL_POINTER_VALUE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/const.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/const.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/const.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/barrier.h \
    $(wildcard include/config/CPU_32v6K) \
    $(wildcard include/config/THUMB2_KERNEL) \
    $(wildcard include/config/CPU_XSC3) \
    $(wildcard include/config/CPU_FA526) \
    $(wildcard include/config/ARM_HEAVY_MB) \
    $(wildcard include/config/ARM_DMA_MEM_BUFFERABLE) \
    $(wildcard include/config/CPU_SPECTRE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/barrier.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpumask.h \
    $(wildcard include/config/FORCE_NR_CPUS) \
    $(wildcard include/config/HOTPLUG_CPU) \
    $(wildcard include/config/DEBUG_PER_CPU_MAPS) \
    $(wildcard include/config/CPUMASK_OFFSTACK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cleanup.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kernel.h \
    $(wildcard include/config/PREEMPT_VOLUNTARY_BUILD) \
    $(wildcard include/config/PREEMPT_DYNAMIC) \
    $(wildcard include/config/HAVE_PREEMPT_DYNAMIC_CALL) \
    $(wildcard include/config/HAVE_PREEMPT_DYNAMIC_KEY) \
    $(wildcard include/config/PREEMPT_) \
    $(wildcard include/config/TRACING) \
    $(wildcard include/config/FTRACE_MCOUNT_RECORD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stdarg.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/align.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/array_size.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/limits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/limits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/limits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/linkage.h \
    $(wildcard include/config/ARCH_USE_SYM_ANNOTATIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stringify.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/export.h \
    $(wildcard include/config/MODVERSIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/linkage.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bitops.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/bits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/bits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/overflow.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/typecheck.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/kernel.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sysinfo.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/generic-non-atomic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/bitops.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqflags.h \
    $(wildcard include/config/TRACE_IRQFLAGS) \
    $(wildcard include/config/PREEMPT_RT) \
    $(wildcard include/config/IRQSOFF_TRACER) \
    $(wildcard include/config/PREEMPT_TRACER) \
    $(wildcard include/config/DEBUG_IRQFLAGS) \
    $(wildcard include/config/TRACE_IRQFLAGS_SUPPORT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqflags_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/irqflags.h \
    $(wildcard include/config/CPU_V7M) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/ptrace.h \
    $(wildcard include/config/ARM_THUMB) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/ptrace.h \
    $(wildcard include/config/CPU_ENDIAN_BE8) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/hwcap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/hwcap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bitfield.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/byteorder.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/byteorder/little_endian.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/byteorder/little_endian.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/swab.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/swab.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/swab.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/swab.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/byteorder/generic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/irqflags.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/percpu.h \
    $(wildcard include/config/CPU_V6) \
    $(wildcard include/config/ARM_HAS_GROUP_RELOCS) \
    $(wildcard include/config/ARM_MODULE_PLTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/insn.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/percpu.h \
    $(wildcard include/config/HAVE_SETUP_PER_CPU_AREA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/threads.h \
    $(wildcard include/config/NR_CPUS) \
    $(wildcard include/config/BASE_SMALL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu-defs.h \
    $(wildcard include/config/DEBUG_FORCE_WEAK_PER_CPU) \
    $(wildcard include/config/AMD_MEM_ENCRYPT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/non-atomic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/non-instrumented-non-atomic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/builtin-__fls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/builtin-__ffs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/builtin-fls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/builtin-ffs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/ffz.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/fls64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/sched.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/hweight.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/arch_hweight.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/const_hweight.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/lock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/atomic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/atomic.h \
    $(wildcard include/config/GENERIC_ATOMIC64) \
    $(wildcard include/config/ARM_LPAE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/prefetch.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/processor.h \
    $(wildcard include/config/HAVE_HW_BREAKPOINT) \
    $(wildcard include/config/BINFMT_ELF_FDPIC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/hw_breakpoint.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/unified.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/vdso/processor.h \
    $(wildcard include/config/ARM_ERRATA_754327) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cache.h \
    $(wildcard include/config/ARM_L1_CACHE_SHIFT) \
    $(wildcard include/config/AEABI) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cmpxchg.h \
    $(wildcard include/config/CPU_SA1100) \
    $(wildcard include/config/CPU_SA110) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cmpxchg-emu.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/cmpxchg-local.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/atomic/atomic-arch-fallback.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/atomic/atomic-long.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/atomic/atomic-instrumented.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/instrumented.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kmsan-checks.h \
    $(wildcard include/config/KMSAN) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/instrumented-lock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/le.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/ext2-atomic-setbit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hex.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kstrtox.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/log2.h \
    $(wildcard include/config/ARCH_HAS_ILOG2_U32) \
    $(wildcard include/config/ARCH_HAS_ILOG2_U64) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/math.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/div64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/compiler.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/div64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/minmax.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/panic.h \
    $(wildcard include/config/PANIC_TIMEOUT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/printk.h \
    $(wildcard include/config/MESSAGE_LOGLEVEL_DEFAULT) \
    $(wildcard include/config/CONSOLE_LOGLEVEL_DEFAULT) \
    $(wildcard include/config/CONSOLE_LOGLEVEL_QUIET) \
    $(wildcard include/config/EARLY_PRINTK) \
    $(wildcard include/config/PRINTK) \
    $(wildcard include/config/PRINTK_INDEX) \
    $(wildcard include/config/DYNAMIC_DEBUG) \
    $(wildcard include/config/DYNAMIC_DEBUG_CORE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/init.h \
    $(wildcard include/config/MEMORY_HOTPLUG) \
    $(wildcard include/config/HAVE_ARCH_PREL32_RELOCATIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kern_levels.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ratelimit_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/param.h \
  arch/arm/include/generated/uapi/asm/param.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/param.h \
    $(wildcard include/config/HZ) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/param.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/spinlock_types_raw.h \
    $(wildcard include/config/DEBUG_SPINLOCK) \
    $(wildcard include/config/DEBUG_LOCK_ALLOC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/spinlock_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/lockdep_types.h \
    $(wildcard include/config/PROVE_RAW_LOCK_NESTING) \
    $(wildcard include/config/LOCK_STAT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/once_lite.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sprintf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/static_call_types.h \
    $(wildcard include/config/HAVE_STATIC_CALL) \
    $(wildcard include/config/HAVE_STATIC_CALL_INLINE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/instruction_pointer.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/wordpart.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bitmap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/find.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/string.h \
    $(wildcard include/config/BINARY_PRINTF) \
    $(wildcard include/config/FORTIFY_SOURCE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/args.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/err.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/string.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/string.h \
    $(wildcard include/config/KASAN) \
    $(wildcard include/config/BCM2835_FAST_MEMCPY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bitmap-str.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpumask_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bug.h \
    $(wildcard include/config/GENERIC_BUG) \
    $(wildcard include/config/BUG_ON_DATA_CORRUPTION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/bug.h \
    $(wildcard include/config/DEBUG_BUGVERBOSE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/opcodes.h \
    $(wildcard include/config/CPU_ENDIAN_BE32) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bug.h \
    $(wildcard include/config/BUG) \
    $(wildcard include/config/GENERIC_BUG_RELATIVE_POINTERS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/instrumentation.h \
    $(wildcard include/config/NOINSTR_VALIDATION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/gfp_types.h \
    $(wildcard include/config/KASAN_HW_TAGS) \
    $(wildcard include/config/SLAB_OBJ_EXT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/numa.h \
    $(wildcard include/config/NODES_SHIFT) \
    $(wildcard include/config/NUMA_KEEP_MEMINFO) \
    $(wildcard include/config/HAVE_ARCH_NODE_DEV_GROUP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/smp_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/llist.h \
    $(wildcard include/config/ARCH_HAVE_NMI_SAFE_CMPXCHG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/preempt.h \
    $(wildcard include/config/PREEMPT_COUNT) \
    $(wildcard include/config/TRACE_PREEMPT_TOGGLE) \
    $(wildcard include/config/PREEMPT_NOTIFIERS) \
    $(wildcard include/config/PREEMPT_NONE) \
    $(wildcard include/config/PREEMPT_VOLUNTARY) \
    $(wildcard include/config/PREEMPT) \
  arch/arm/include/generated/asm/preempt.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/preempt.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/thread_info.h \
    $(wildcard include/config/THREAD_INFO_IN_TASK) \
    $(wildcard include/config/GENERIC_ENTRY) \
    $(wildcard include/config/HAVE_ARCH_WITHIN_STACK_FRAMES) \
    $(wildcard include/config/HARDENED_USERCOPY) \
    $(wildcard include/config/SH) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/restart_block.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/current.h \
    $(wildcard include/config/CURRENT_POINTER_IN_TPIDRURO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/thread_info.h \
    $(wildcard include/config/VMAP_STACK) \
    $(wildcard include/config/ARM_THUMBEE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/fpstate.h \
    $(wildcard include/config/VFPv3) \
    $(wildcard include/config/IWMMXT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/page.h \
    $(wildcard include/config/PAGE_SHIFT) \
    $(wildcard include/config/CPU_COPY_V4WT) \
    $(wildcard include/config/CPU_COPY_V4WB) \
    $(wildcard include/config/CPU_COPY_FEROCEON) \
    $(wildcard include/config/CPU_COPY_FA) \
    $(wildcard include/config/CPU_XSCALE) \
    $(wildcard include/config/CPU_COPY_V6) \
    $(wildcard include/config/KUSER_HELPERS) \
    $(wildcard include/config/HAVE_ARCH_PFN_VALID) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/glue.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/pgtable-3level-types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/memory.h \
    $(wildcard include/config/NEED_MACH_MEMORY_H) \
    $(wildcard include/config/PAGE_OFFSET) \
    $(wildcard include/config/HIGHMEM) \
    $(wildcard include/config/DRAM_BASE) \
    $(wildcard include/config/DRAM_SIZE) \
    $(wildcard include/config/XIP_KERNEL) \
    $(wildcard include/config/HAVE_TCM) \
    $(wildcard include/config/ARM_PATCH_PHYS_VIRT) \
    $(wildcard include/config/PHYS_OFFSET) \
    $(wildcard include/config/DEBUG_VIRTUAL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sizes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/kasan_def.h \
    $(wildcard include/config/KASAN_SHADOW_OFFSET) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/getorder.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/memory_model.h \
    $(wildcard include/config/FLATMEM) \
    $(wildcard include/config/SPARSEMEM_VMEMMAP) \
    $(wildcard include/config/SPARSEMEM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pfn.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/traps.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/smp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu.h \
    $(wildcard include/config/MODULES) \
    $(wildcard include/config/MEM_ALLOC_PROFILING) \
    $(wildcard include/config/RANDOM_KMALLOC_CACHES) \
    $(wildcard include/config/PAGE_SIZE_4KB) \
    $(wildcard include/config/NEED_PER_CPU_PAGE_FIRST_CHUNK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/alloc_tag.h \
    $(wildcard include/config/MEM_ALLOC_PROFILING_DEBUG) \
    $(wildcard include/config/MEM_ALLOC_PROFILING_ENABLED_BY_DEFAULT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/codetag.h \
    $(wildcard include/config/CODE_TAGGING) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/static_key.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/jump_label.h \
    $(wildcard include/config/JUMP_LABEL) \
    $(wildcard include/config/HAVE_ARCH_JUMP_LABEL_RELATIVE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/jump_label.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmdebug.h \
    $(wildcard include/config/DEBUG_VM) \
    $(wildcard include/config/DEBUG_VM_IRQSOFF) \
    $(wildcard include/config/DEBUG_VM_PGFLAGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched.h \
    $(wildcard include/config/SCHED_INFO) \
    $(wildcard include/config/SCHEDSTATS) \
    $(wildcard include/config/FAIR_GROUP_SCHED) \
    $(wildcard include/config/RT_GROUP_SCHED) \
    $(wildcard include/config/RT_MUTEXES) \
    $(wildcard include/config/UCLAMP_TASK) \
    $(wildcard include/config/UCLAMP_BUCKETS_COUNT) \
    $(wildcard include/config/KMAP_LOCAL) \
    $(wildcard include/config/SCHED_CLASS_EXT) \
    $(wildcard include/config/CGROUP_SCHED) \
    $(wildcard include/config/BLK_DEV_IO_TRACE) \
    $(wildcard include/config/PREEMPT_RCU) \
    $(wildcard include/config/TASKS_RCU) \
    $(wildcard include/config/TASKS_TRACE_RCU) \
    $(wildcard include/config/MEMCG_V1) \
    $(wildcard include/config/CGROUPS) \
    $(wildcard include/config/BLK_CGROUP) \
    $(wildcard include/config/PSI) \
    $(wildcard include/config/PAGE_OWNER) \
    $(wildcard include/config/EVENTFD) \
    $(wildcard include/config/ARCH_HAS_CPU_PASID) \
    $(wildcard include/config/CPU_SUP_INTEL) \
    $(wildcard include/config/TASK_DELAY_ACCT) \
    $(wildcard include/config/STACKPROTECTOR) \
    $(wildcard include/config/ARCH_HAS_SCALED_CPUTIME) \
    $(wildcard include/config/NO_HZ_FULL) \
    $(wildcard include/config/POSIX_CPUTIMERS) \
    $(wildcard include/config/POSIX_CPU_TIMERS_TASK_WORK) \
    $(wildcard include/config/KEYS) \
    $(wildcard include/config/SYSVIPC) \
    $(wildcard include/config/DETECT_HUNG_TASK) \
    $(wildcard include/config/IO_URING) \
    $(wildcard include/config/AUDIT) \
    $(wildcard include/config/AUDITSYSCALL) \
    $(wildcard include/config/DEBUG_MUTEXES) \
    $(wildcard include/config/UBSAN) \
    $(wildcard include/config/UBSAN_TRAP) \
    $(wildcard include/config/COMPACTION) \
    $(wildcard include/config/TASK_XACCT) \
    $(wildcard include/config/CPUSETS) \
    $(wildcard include/config/X86_CPU_RESCTRL) \
    $(wildcard include/config/FUTEX) \
    $(wildcard include/config/COMPAT) \
    $(wildcard include/config/PERF_EVENTS) \
    $(wildcard include/config/RSEQ) \
    $(wildcard include/config/SCHED_MM_CID) \
    $(wildcard include/config/FAULT_INJECTION) \
    $(wildcard include/config/LATENCYTOP) \
    $(wildcard include/config/KUNIT) \
    $(wildcard include/config/FUNCTION_GRAPH_TRACER) \
    $(wildcard include/config/KCOV) \
    $(wildcard include/config/MEMCG) \
    $(wildcard include/config/UPROBES) \
    $(wildcard include/config/BCACHE) \
    $(wildcard include/config/LIVEPATCH) \
    $(wildcard include/config/SECURITY) \
    $(wildcard include/config/BPF_SYSCALL) \
    $(wildcard include/config/GCC_PLUGIN_STACKLEAK) \
    $(wildcard include/config/X86_MCE) \
    $(wildcard include/config/KRETPROBES) \
    $(wildcard include/config/RETHOOK) \
    $(wildcard include/config/ARCH_HAS_PARANOID_L1D_FLUSH) \
    $(wildcard include/config/RV) \
    $(wildcard include/config/USER_EVENTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sched.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cache.h \
    $(wildcard include/config/ARCH_HAS_CACHE_LINE_SIZE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pid_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sem_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/shm.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/shmparam.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kmsan_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mutex_types.h \
    $(wildcard include/config/MUTEX_SPIN_ON_OWNER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/osq_lock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/spinlock_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rwlock_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/plist_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hrtimer_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/timerqueue_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rbtree_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/timer_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seccomp_types.h \
    $(wildcard include/config/SECCOMP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/nodemask_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/refcount_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/resource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/resource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/time_types.h \
  arch/arm/include/generated/uapi/asm/resource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/resource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/resource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/latencytop.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/prio.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/signal_types.h \
    $(wildcard include/config/OLD_SIGACTION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/signal.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/signal.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/signal.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/signal-defs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/sigcontext.h \
  arch/arm/include/generated/uapi/asm/siginfo.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/siginfo.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/syscall_user_dispatch_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mm_types_task.h \
    $(wildcard include/config/ARCH_WANT_BATCHED_UNMAP_TLB_FLUSH) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netdevice_xmit.h \
    $(wildcard include/config/NET_EGRESS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/task_io_accounting.h \
    $(wildcard include/config/TASK_IO_ACCOUNTING) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/posix-timers_types.h \
    $(wildcard include/config/POSIX_TIMERS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/rseq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seqlock_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kcsan.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rv.h \
    $(wildcard include/config/RV_REACTORS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/livepatch_sched.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uidgid_types.h \
  arch/arm/include/generated/asm/kmap_size.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/kmap_size.h \
    $(wildcard include/config/DEBUG_KMAP_LOCAL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/ext.h \
    $(wildcard include/config/EXT_GROUP_SCHED) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/spinlock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bottom_half.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/lockdep.h \
    $(wildcard include/config/DEBUG_LOCKING_API_SELFTESTS) \
  arch/arm/include/generated/asm/mmiowb.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/mmiowb.h \
    $(wildcard include/config/MMIOWB) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/spinlock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rwlock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/spinlock_api_smp.h \
    $(wildcard include/config/INLINE_SPIN_LOCK) \
    $(wildcard include/config/INLINE_SPIN_LOCK_BH) \
    $(wildcard include/config/INLINE_SPIN_LOCK_IRQ) \
    $(wildcard include/config/INLINE_SPIN_LOCK_IRQSAVE) \
    $(wildcard include/config/INLINE_SPIN_TRYLOCK) \
    $(wildcard include/config/INLINE_SPIN_TRYLOCK_BH) \
    $(wildcard include/config/UNINLINE_SPIN_UNLOCK) \
    $(wildcard include/config/INLINE_SPIN_UNLOCK_BH) \
    $(wildcard include/config/INLINE_SPIN_UNLOCK_IRQ) \
    $(wildcard include/config/INLINE_SPIN_UNLOCK_IRQRESTORE) \
    $(wildcard include/config/GENERIC_LOCKBREAK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rwlock_api_smp.h \
    $(wildcard include/config/INLINE_READ_LOCK) \
    $(wildcard include/config/INLINE_WRITE_LOCK) \
    $(wildcard include/config/INLINE_READ_LOCK_BH) \
    $(wildcard include/config/INLINE_WRITE_LOCK_BH) \
    $(wildcard include/config/INLINE_READ_LOCK_IRQ) \
    $(wildcard include/config/INLINE_WRITE_LOCK_IRQ) \
    $(wildcard include/config/INLINE_READ_LOCK_IRQSAVE) \
    $(wildcard include/config/INLINE_WRITE_LOCK_IRQSAVE) \
    $(wildcard include/config/INLINE_READ_TRYLOCK) \
    $(wildcard include/config/INLINE_WRITE_TRYLOCK) \
    $(wildcard include/config/INLINE_READ_UNLOCK) \
    $(wildcard include/config/INLINE_WRITE_UNLOCK) \
    $(wildcard include/config/INLINE_READ_UNLOCK_BH) \
    $(wildcard include/config/INLINE_WRITE_UNLOCK_BH) \
    $(wildcard include/config/INLINE_READ_UNLOCK_IRQ) \
    $(wildcard include/config/INLINE_WRITE_UNLOCK_IRQ) \
    $(wildcard include/config/INLINE_READ_UNLOCK_IRQRESTORE) \
    $(wildcard include/config/INLINE_WRITE_UNLOCK_IRQRESTORE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/interrupt.h \
    $(wildcard include/config/IRQ_FORCED_THREADING) \
    $(wildcard include/config/GENERIC_IRQ_PROBE) \
    $(wildcard include/config/PROC_FS) \
    $(wildcard include/config/IRQ_TIMINGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqreturn.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqnr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/irqnr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hardirq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/context_tracking_state.h \
    $(wildcard include/config/CONTEXT_TRACKING_USER) \
    $(wildcard include/config/CONTEXT_TRACKING) \
    $(wildcard include/config/CONTEXT_TRACKING_IDLE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/context_tracking_irq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ftrace_irq.h \
    $(wildcard include/config/HWLAT_TRACER) \
    $(wildcard include/config/OSNOISE_TRACER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vtime.h \
    $(wildcard include/config/VIRT_CPU_ACCOUNTING) \
    $(wildcard include/config/IRQ_TIME_ACCOUNTING) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/hardirq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/irq.h \
    $(wildcard include/config/SPARSE_IRQ) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/hardirq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irq.h \
    $(wildcard include/config/GENERIC_IRQ_EFFECTIVE_AFF_MASK) \
    $(wildcard include/config/GENERIC_IRQ_IPI) \
    $(wildcard include/config/IRQ_DOMAIN_HIERARCHY) \
    $(wildcard include/config/DEPRECATED_IRQ_CPU_ONOFFLINE) \
    $(wildcard include/config/GENERIC_IRQ_MIGRATION) \
    $(wildcard include/config/GENERIC_PENDING_IRQ) \
    $(wildcard include/config/HARDIRQS_SW_RESEND) \
    $(wildcard include/config/GENERIC_IRQ_LEGACY) \
    $(wildcard include/config/GENERIC_IRQ_CHIP) \
    $(wildcard include/config/GENERIC_IRQ_MULTI_HANDLER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqhandler.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/topology.h \
    $(wildcard include/config/USE_PERCPU_NUMA_NODE_ID) \
    $(wildcard include/config/HAVE_MEMORYLESS_NODES) \
    $(wildcard include/config/SCHED_SMT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/arch_topology.h \
    $(wildcard include/config/GENERIC_ARCH_TOPOLOGY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmzone.h \
    $(wildcard include/config/ARCH_FORCE_MAX_ORDER) \
    $(wildcard include/config/CMA) \
    $(wildcard include/config/MEMORY_ISOLATION) \
    $(wildcard include/config/ZSMALLOC) \
    $(wildcard include/config/UNACCEPTED_MEMORY) \
    $(wildcard include/config/SHADOW_CALL_STACK) \
    $(wildcard include/config/IOMMU_SUPPORT) \
    $(wildcard include/config/SWAP) \
    $(wildcard include/config/LRU_GEN_STATS) \
    $(wildcard include/config/LRU_GEN_WALKS_MMU) \
    $(wildcard include/config/ZONE_DMA) \
    $(wildcard include/config/ZONE_DMA32) \
    $(wildcard include/config/ZONE_DEVICE) \
    $(wildcard include/config/MEMORY_FAILURE) \
    $(wildcard include/config/PAGE_EXTENSION) \
    $(wildcard include/config/DEFERRED_STRUCT_PAGE_INIT) \
    $(wildcard include/config/SPARSEMEM_EXTREME) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/list_nulls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/wait.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seqlock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mutex.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/debug_locks.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/nodemask.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/random.h \
    $(wildcard include/config/VMGENID) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/random.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ioctl.h \
  arch/arm/include/generated/uapi/asm/ioctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/ioctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/ioctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/prandom.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/once.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pageblock-flags.h \
    $(wildcard include/config/HUGETLB_PAGE) \
    $(wildcard include/config/HUGETLB_PAGE_SIZE_VARIABLE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page-flags-layout.h \
  include/generated/bounds.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mm_types.h \
    $(wildcard include/config/HAVE_ALIGNED_STRUCT_PAGE) \
    $(wildcard include/config/HUGETLB_PMD_PAGE_TABLE_SHARING) \
    $(wildcard include/config/USERFAULTFD) \
    $(wildcard include/config/ANON_VMA_NAME) \
    $(wildcard include/config/HAVE_ARCH_COMPAT_MMAP_BASES) \
    $(wildcard include/config/MEMBARRIER) \
    $(wildcard include/config/AIO) \
    $(wildcard include/config/MMU_NOTIFIER) \
    $(wildcard include/config/SPLIT_PMD_PTLOCKS) \
    $(wildcard include/config/IOMMU_MM_DATA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/auxvec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/auxvec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/auxvec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/auxvec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kref.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/refcount.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rbtree.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcupdate.h \
    $(wildcard include/config/TINY_RCU) \
    $(wildcard include/config/RCU_STRICT_GRACE_PERIOD) \
    $(wildcard include/config/RCU_LAZY) \
    $(wildcard include/config/TASKS_RCU_GENERIC) \
    $(wildcard include/config/RCU_STALL_COMMON) \
    $(wildcard include/config/KVM_XFER_TO_GUEST_WORK) \
    $(wildcard include/config/RCU_NOCB_CPU) \
    $(wildcard include/config/TASKS_RUDE_RCU) \
    $(wildcard include/config/TREE_RCU) \
    $(wildcard include/config/DEBUG_OBJECTS_RCU_HEAD) \
    $(wildcard include/config/PROVE_RCU) \
    $(wildcard include/config/ARCH_WEAK_RELEASE_ACQUIRE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcutree.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/maple_tree.h \
    $(wildcard include/config/MAPLE_RCU_DISABLED) \
    $(wildcard include/config/DEBUG_MAPLE_TREE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rwsem.h \
    $(wildcard include/config/RWSEM_SPIN_ON_OWNER) \
    $(wildcard include/config/DEBUG_RWSEMS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/completion.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/swait.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uprobes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/uprobes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/probes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/workqueue.h \
    $(wildcard include/config/DEBUG_OBJECTS_WORK) \
    $(wildcard include/config/FREEZER) \
    $(wildcard include/config/SYSFS) \
    $(wildcard include/config/WQ_WATCHDOG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/timer.h \
    $(wildcard include/config/DEBUG_OBJECTS_TIMERS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ktime.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/jiffies.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/math64.h \
    $(wildcard include/config/ARCH_SUPPORTS_INT128) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/math64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/time.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/time64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/time64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/time.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/time32.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/timex.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/timex.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/timex.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/time32.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/time.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/jiffies.h \
  include/generated/timeconst.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/ktime.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/timekeeping.h \
    $(wildcard include/config/GENERIC_CMOS_UPDATE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/clocksource_ids.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/debugobjects.h \
    $(wildcard include/config/DEBUG_OBJECTS) \
    $(wildcard include/config/DEBUG_OBJECTS_FREE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/workqueue_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu_counter.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/mmu.h \
    $(wildcard include/config/CPU_HAS_ASID) \
    $(wildcard include/config/VDSO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page-flags.h \
    $(wildcard include/config/PAGE_IDLE_FLAG) \
    $(wildcard include/config/ARCH_USES_PG_ARCH_2) \
    $(wildcard include/config/ARCH_USES_PG_ARCH_3) \
    $(wildcard include/config/HUGETLB_PAGE_OPTIMIZE_VMEMMAP) \
    $(wildcard include/config/DEBUG_KMAP_LOCAL_FORCE_MAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/local_lock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/local_lock_internal.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/zswap.h \
    $(wildcard include/config/ZSWAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/memory_hotplug.h \
    $(wildcard include/config/ARCH_HAS_ADD_PAGES) \
    $(wildcard include/config/MEMORY_HOTREMOVE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/notifier.h \
    $(wildcard include/config/TREE_SRCU) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/srcu.h \
    $(wildcard include/config/TINY_SRCU) \
    $(wildcard include/config/NEED_SRCU_NMI_SAFE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcu_segcblist.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/srcutree.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcu_node_tree.h \
    $(wildcard include/config/RCU_FANOUT) \
    $(wildcard include/config/RCU_FANOUT_LEAF) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/topology.h \
    $(wildcard include/config/ARM_CPU_TOPOLOGY) \
    $(wildcard include/config/BL_SWITCHER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/topology.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/io.h \
    $(wildcard include/config/HAS_IOPORT_MAP) \
    $(wildcard include/config/PCI) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/io.h \
    $(wildcard include/config/PCMCIA) \
    $(wildcard include/config/NEED_MACH_IO_H) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/pci_iomap.h \
    $(wildcard include/config/NO_GENERIC_PCI_IOPORT_MAP) \
    $(wildcard include/config/GENERIC_PCI_IOMAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/io.h \
    $(wildcard include/config/GENERIC_IOMAP) \
    $(wildcard include/config/TRACE_MMIO_ACCESS) \
    $(wildcard include/config/GENERIC_IOREMAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/logic_pio.h \
    $(wildcard include/config/INDIRECT_PIO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fwnode.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/slab.h \
    $(wildcard include/config/FAILSLAB) \
    $(wildcard include/config/KFENCE) \
    $(wildcard include/config/SLUB_TINY) \
    $(wildcard include/config/SLUB_DEBUG) \
    $(wildcard include/config/SLAB_FREELIST_HARDENED) \
    $(wildcard include/config/SLAB_BUCKETS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/gfp.h \
    $(wildcard include/config/CONTIG_ALLOC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu-refcount.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hash.h \
    $(wildcard include/config/HAVE_ARCH_HASH) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kasan.h \
    $(wildcard include/config/KASAN_STACK) \
    $(wildcard include/config/KASAN_VMALLOC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kasan-enabled.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kasan-tags.h \
  arch/arm/include/generated/asm/irq_regs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/irq_regs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqdesc.h \
    $(wildcard include/config/PM_SLEEP) \
    $(wildcard include/config/GENERIC_IRQ_DEBUGFS) \
    $(wildcard include/config/IRQ_DOMAIN) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kobject.h \
    $(wildcard include/config/UEVENT_HELPER) \
    $(wildcard include/config/DEBUG_KOBJECT_RELEASE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sysfs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kernfs.h \
    $(wildcard include/config/KERNFS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/idr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/radix-tree.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/xarray.h \
    $(wildcard include/config/XARRAY_MULTI) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/mm.h \
    $(wildcard include/config/MMU_LAZY_TLB_REFCOUNT) \
    $(wildcard include/config/ARCH_HAS_MEMBARRIER_CALLBACKS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sync_core.h \
    $(wildcard include/config/ARCH_HAS_SYNC_CORE_BEFORE_USERMODE) \
    $(wildcard include/config/ARCH_HAS_PREPARE_SYNC_CORE_CMD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/coredump.h \
    $(wildcard include/config/CORE_DUMP_DEFAULT_ELF_HEADERS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uidgid.h \
    $(wildcard include/config/MULTIUSER) \
    $(wildcard include/config/USER_NS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/highuid.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kobject_ns.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/stat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/stat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/hw_irq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hrtimer.h \
    $(wildcard include/config/HIGH_RES_TIMERS) \
    $(wildcard include/config/TIME_LOW_RES) \
    $(wildcard include/config/TIMERFD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hrtimer_defs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/timerqueue.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/sections.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/sections.h \
    $(wildcard include/config/HAVE_FUNCTION_DESCRIPTORS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mm.h \
    $(wildcard include/config/SYSCTL) \
    $(wildcard include/config/HAVE_ARCH_MMAP_RND_BITS) \
    $(wildcard include/config/HAVE_ARCH_MMAP_RND_COMPAT_BITS) \
    $(wildcard include/config/MEM_SOFT_DIRTY) \
    $(wildcard include/config/ARCH_USES_HIGH_VMA_FLAGS) \
    $(wildcard include/config/ARCH_HAS_PKEYS) \
    $(wildcard include/config/ARCH_PKEY_BITS) \
    $(wildcard include/config/X86_USER_SHADOW_STACK) \
    $(wildcard include/config/X86) \
    $(wildcard include/config/PPC64) \
    $(wildcard include/config/PARISC) \
    $(wildcard include/config/SPARC64) \
    $(wildcard include/config/ARM64_MTE) \
    $(wildcard include/config/HAVE_ARCH_USERFAULTFD_MINOR) \
    $(wildcard include/config/PPC32) \
    $(wildcard include/config/STACK_GROWSUP) \
    $(wildcard include/config/SHMEM) \
    $(wildcard include/config/FS_DAX) \
    $(wildcard include/config/MIGRATION) \
    $(wildcard include/config/ARCH_HAS_GIGANTIC_PAGE) \
    $(wildcard include/config/ARCH_SUPPORTS_PMD_PFNMAP) \
    $(wildcard include/config/ARCH_SUPPORTS_PUD_PFNMAP) \
    $(wildcard include/config/ARCH_HAS_PTE_DEVMAP) \
    $(wildcard include/config/HIGHPTE) \
    $(wildcard include/config/DEBUG_VM_RB) \
    $(wildcard include/config/PAGE_POISONING) \
    $(wildcard include/config/INIT_ON_ALLOC_DEFAULT_ON) \
    $(wildcard include/config/INIT_ON_FREE_DEFAULT_ON) \
    $(wildcard include/config/DEBUG_PAGEALLOC) \
    $(wildcard include/config/ARCH_WANT_OPTIMIZE_DAX_VMEMMAP) \
    $(wildcard include/config/MAPPING_DIRTY_HELPERS) \
    $(wildcard include/config/PAGE_POOL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pgalloc_tag.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmap_lock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/tracepoint-defs.h \
    $(wildcard include/config/TRACEPOINTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/range.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bit_spinlock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/shrinker.h \
    $(wildcard include/config/SHRINKER_DEBUG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page_ext.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stacktrace.h \
    $(wildcard include/config/ARCH_STACKWALK) \
    $(wildcard include/config/STACKTRACE) \
    $(wildcard include/config/HAVE_RELIABLE_STACKTRACE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page_ref.h \
    $(wildcard include/config/DEBUG_PAGE_REF) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pgtable.h \
    $(wildcard include/config/PGTABLE_LEVELS) \
    $(wildcard include/config/ARCH_HAS_NONLEAF_PMD_YOUNG) \
    $(wildcard include/config/ARCH_HAS_HW_PTE_YOUNG) \
    $(wildcard include/config/GUP_GET_PXX_LOW_HIGH) \
    $(wildcard include/config/ARCH_WANT_PMD_MKWRITE) \
    $(wildcard include/config/HAVE_ARCH_SOFT_DIRTY) \
    $(wildcard include/config/ARCH_ENABLE_THP_MIGRATION) \
    $(wildcard include/config/HAVE_ARCH_HUGE_VMAP) \
    $(wildcard include/config/X86_ESPFIX64) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/pgtable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/proc-fns.h \
    $(wildcard include/config/BIG_LITTLE) \
    $(wildcard include/config/HARDEN_BRANCH_PREDICTOR) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/glue-proc.h \
    $(wildcard include/config/CPU_ARM7TDMI) \
    $(wildcard include/config/CPU_ARM720T) \
    $(wildcard include/config/CPU_ARM740T) \
    $(wildcard include/config/CPU_ARM9TDMI) \
    $(wildcard include/config/CPU_ARM920T) \
    $(wildcard include/config/CPU_ARM922T) \
    $(wildcard include/config/CPU_ARM925T) \
    $(wildcard include/config/CPU_ARM926T) \
    $(wildcard include/config/CPU_ARM940T) \
    $(wildcard include/config/CPU_ARM946E) \
    $(wildcard include/config/CPU_ARM1020) \
    $(wildcard include/config/CPU_ARM1020E) \
    $(wildcard include/config/CPU_ARM1022) \
    $(wildcard include/config/CPU_ARM1026) \
    $(wildcard include/config/CPU_MOHAWK) \
    $(wildcard include/config/CPU_FEROCEON) \
    $(wildcard include/config/CPU_V6K) \
    $(wildcard include/config/CPU_PJ4B) \
    $(wildcard include/config/CPU_V7) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/pgtable-nopud.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/pgtable-nop4d.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/pgtable-hwdef.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/pgtable-3level-hwdef.h \
    $(wildcard include/config/CPU_TTBR0_PAN) \
    $(wildcard include/config/VMSPLIT_2G) \
    $(wildcard include/config/VMSPLIT_3G) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/tlbflush.h \
    $(wildcard include/config/SMP_ON_UP) \
    $(wildcard include/config/CPU_TLB_V4WT) \
    $(wildcard include/config/CPU_TLB_FA) \
    $(wildcard include/config/CPU_TLB_V4WBI) \
    $(wildcard include/config/CPU_TLB_FEROCEON) \
    $(wildcard include/config/CPU_TLB_V4WB) \
    $(wildcard include/config/CPU_TLB_V6) \
    $(wildcard include/config/CPU_TLB_V7) \
    $(wildcard include/config/ARM_ERRATA_720789) \
    $(wildcard include/config/ARM_ERRATA_798181) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/pgtable-3level.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/pgtable_uffd.h \
    $(wildcard include/config/HAVE_ARCH_USERFAULTFD_WP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page_table_check.h \
    $(wildcard include/config/PAGE_TABLE_CHECK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/memremap.h \
    $(wildcard include/config/DEVICE_PRIVATE) \
    $(wildcard include/config/PCI_P2PDMA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ioport.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/huge_mm.h \
    $(wildcard include/config/READ_ONLY_THP_FOR_FS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fs.h \
    $(wildcard include/config/FS_POSIX_ACL) \
    $(wildcard include/config/CGROUP_WRITEBACK) \
    $(wildcard include/config/IMA) \
    $(wildcard include/config/FILE_LOCKING) \
    $(wildcard include/config/FSNOTIFY) \
    $(wildcard include/config/FS_ENCRYPTION) \
    $(wildcard include/config/FS_VERITY) \
    $(wildcard include/config/EPOLL) \
    $(wildcard include/config/UNICODE) \
    $(wildcard include/config/QUOTA) \
    $(wildcard include/config/BLOCK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/wait_bit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kdev_t.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/kdev_t.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dcache.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rculist.h \
    $(wildcard include/config/PROVE_RCU_LIST) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rculist_bl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/list_bl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/lockref.h \
    $(wildcard include/config/ARCH_USE_CMPXCHG_LOCKREF) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stringhash.h \
    $(wildcard include/config/DCACHE_WORD_ACCESS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/path.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/list_lru.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pid.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/capability.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/capability.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/semaphore.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fcntl.h \
    $(wildcard include/config/ARCH_32BIT_OFF_T) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/fcntl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/fcntl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/fcntl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/openat2.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/migrate_mode.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu-rwsem.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcuwait.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/signal.h \
    $(wildcard include/config/SCHED_AUTOGROUP) \
    $(wildcard include/config/BSD_PROCESS_ACCT) \
    $(wildcard include/config/TASKSTATS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/signal.h \
    $(wildcard include/config/DYNAMIC_SIGFRAME) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/jobctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/task.h \
    $(wildcard include/config/HAVE_EXIT_THREAD) \
    $(wildcard include/config/ARCH_WANTS_DYNAMIC_TASK_STRUCT) \
    $(wildcard include/config/HAVE_ARCH_THREAD_STRUCT_WHITELIST) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uaccess.h \
    $(wildcard include/config/ARCH_HAS_SUBPAGE_FAULTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fault-inject-usercopy.h \
    $(wildcard include/config/FAULT_INJECTION_USERCOPY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/nospec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/uaccess.h \
    $(wildcard include/config/CPU_SW_DOMAIN_PAN) \
    $(wildcard include/config/HAVE_EFFICIENT_UNALIGNED_ACCESS) \
    $(wildcard include/config/UACCESS_WITH_MEMCPY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/domain.h \
    $(wildcard include/config/IO_36) \
    $(wildcard include/config/CPU_USE_DOMAINS) \
    $(wildcard include/config/CPU_CP15_MMU) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/unaligned.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/unaligned/packed_struct.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/unaligned.h \
  arch/arm/include/generated/asm/extable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/extable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/access_ok.h \
    $(wildcard include/config/ALTERNATE_USER_ADDRESS_SPACE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cred.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/key.h \
    $(wildcard include/config/KEY_NOTIFICATIONS) \
    $(wildcard include/config/NET) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sysctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sysctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/assoc_array.h \
    $(wildcard include/config/ASSOCIATIVE_ARRAY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/user.h \
    $(wildcard include/config/VFIO_PCI_ZDEV_KVM) \
    $(wildcard include/config/IOMMUFD) \
    $(wildcard include/config/WATCH_QUEUE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ratelimit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/posix-timers.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/alarmtimer.h \
    $(wildcard include/config/RTC_CLASS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcu_sync.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/delayed_call.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uuid.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/errseq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ioprio.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/rt.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/iocontext.h \
    $(wildcard include/config/BLK_ICQ) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ioprio.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fs_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mount.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mnt_idmapping.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rw_hint.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/fs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/quota.h \
    $(wildcard include/config/QUOTA_NETLINK_INTERFACE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/dqblk_xfs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dqblk_v1.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dqblk_v2.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dqblk_qtree.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/projid.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/quota.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/secretmem.h \
    $(wildcard include/config/SECRETMEM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vmstat.h \
    $(wildcard include/config/VM_EVENT_COUNTERS) \
    $(wildcard include/config/DEBUG_TLBFLUSH) \
    $(wildcard include/config/PER_VMA_LOCK_STATS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vm_event_item.h \
    $(wildcard include/config/MEMORY_BALLOON) \
    $(wildcard include/config/BALLOON_COMPACTION) \
    $(wildcard include/config/DEBUG_STACK_USAGE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mm_inline.h \
    $(wildcard include/config/LRU_GEN_ENABLED) \
    $(wildcard include/config/PTE_MARKER_UFFD_WP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/swap.h \
    $(wildcard include/config/THP_SWAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/memcontrol.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cgroup.h \
    $(wildcard include/config/DEBUG_CGROUP_REF) \
    $(wildcard include/config/CGROUP_CPUACCT) \
    $(wildcard include/config/SOCK_CGROUP_DATA) \
    $(wildcard include/config/CGROUP_DATA) \
    $(wildcard include/config/CGROUP_BPF) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/cgroupstats.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/taskstats.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seq_file.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/string_helpers.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ctype.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/string_choices.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ns_common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/nsproxy.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/user_namespace.h \
    $(wildcard include/config/INOTIFY_USER) \
    $(wildcard include/config/FANOTIFY) \
    $(wildcard include/config/BINFMT_MISC) \
    $(wildcard include/config/PERSISTENT_KEYRINGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cgroup-defs.h \
    $(wildcard include/config/CGROUP_NET_CLASSID) \
    $(wildcard include/config/CGROUP_NET_PRIO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/u64_stats_sync.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpf-cgroup-defs.h \
    $(wildcard include/config/BPF_LSM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/psi_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kthread.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cgroup_subsys.h \
    $(wildcard include/config/CGROUP_DEVICE) \
    $(wildcard include/config/CGROUP_FREEZER) \
    $(wildcard include/config/CGROUP_PERF) \
    $(wildcard include/config/CGROUP_HUGETLB) \
    $(wildcard include/config/CGROUP_PIDS) \
    $(wildcard include/config/CGROUP_RDMA) \
    $(wildcard include/config/CGROUP_MISC) \
    $(wildcard include/config/CGROUP_DEBUG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cgroup_refcnt.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page_counter.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vmpressure.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/eventfd.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/eventfd.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/writeback.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/flex_proportions.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/backing-dev-defs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/blk_types.h \
    $(wildcard include/config/FAIL_MAKE_REQUEST) \
    $(wildcard include/config/BLK_CGROUP_IOCOST) \
    $(wildcard include/config/BLK_INLINE_ENCRYPTION) \
    $(wildcard include/config/BLK_DEV_INTEGRITY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bvec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/highmem.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cacheflush.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cacheflush.h \
    $(wildcard include/config/ARM_ERRATA_411920) \
    $(wildcard include/config/CPU_CACHE_VIPT) \
    $(wildcard include/config/OUTER_CACHE) \
    $(wildcard include/config/CPU_ICACHE_MISMATCH_WORKAROUND) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/glue-cache.h \
    $(wildcard include/config/CPU_CACHE_V4) \
    $(wildcard include/config/CPU_CACHE_V4WB) \
    $(wildcard include/config/CACHE_B15_RAC) \
    $(wildcard include/config/CPU_CACHE_NOP) \
    $(wildcard include/config/CPU_CACHE_V7) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cachetype.h \
    $(wildcard include/config/CPU_CACHE_VIVT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/outercache.h \
    $(wildcard include/config/OUTER_CACHE_SYNC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kmsan.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dma-direction.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/highmem-internal.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/highmem.h \
    $(wildcard include/config/DEBUG_HIGHMEM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/fixmap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/fixmap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/device.h \
    $(wildcard include/config/GENERIC_MSI_IRQ) \
    $(wildcard include/config/ENERGY_MODEL) \
    $(wildcard include/config/PINCTRL) \
    $(wildcard include/config/ARCH_HAS_DMA_OPS) \
    $(wildcard include/config/DMA_DECLARE_COHERENT) \
    $(wildcard include/config/DMA_CMA) \
    $(wildcard include/config/SWIOTLB) \
    $(wildcard include/config/SWIOTLB_DYNAMIC) \
    $(wildcard include/config/ARCH_HAS_SYNC_DMA_FOR_DEVICE) \
    $(wildcard include/config/ARCH_HAS_SYNC_DMA_FOR_CPU) \
    $(wildcard include/config/ARCH_HAS_SYNC_DMA_FOR_CPU_ALL) \
    $(wildcard include/config/DMA_OPS_BYPASS) \
    $(wildcard include/config/DMA_NEED_SYNC) \
    $(wildcard include/config/IOMMU_DMA) \
    $(wildcard include/config/PM) \
    $(wildcard include/config/OF) \
    $(wildcard include/config/DEVTMPFS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dev_printk.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/energy_model.h \
    $(wildcard include/config/SCHED_DEBUG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/cpufreq.h \
    $(wildcard include/config/CPU_FREQ) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/topology.h \
    $(wildcard include/config/SCHED_CLUSTER) \
    $(wildcard include/config/SCHED_MC) \
    $(wildcard include/config/CPU_FREQ_GOV_SCHEDUTIL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/idle.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/sd_flags.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/klist.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pm.h \
    $(wildcard include/config/VT_CONSOLE_SLEEP) \
    $(wildcard include/config/CXL_SUSPEND) \
    $(wildcard include/config/PM_CLK) \
    $(wildcard include/config/PM_GENERIC_DOMAINS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/device/bus.h \
    $(wildcard include/config/ACPI) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/device/class.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/device/devres.h \
    $(wildcard include/config/HAS_IOMEM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/device/driver.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/module.h \
    $(wildcard include/config/MODULES_TREE_LOOKUP) \
    $(wildcard include/config/STACKTRACE_BUILD_ID) \
    $(wildcard include/config/ARCH_USES_CFI_TRAPS) \
    $(wildcard include/config/MODULE_SIG) \
    $(wildcard include/config/KALLSYMS) \
    $(wildcard include/config/BPF_EVENTS) \
    $(wildcard include/config/EVENT_TRACING) \
    $(wildcard include/config/KPROBES) \
    $(wildcard include/config/MODULE_UNLOAD) \
    $(wildcard include/config/MITIGATION_ITS) \
    $(wildcard include/config/CONSTRUCTORS) \
    $(wildcard include/config/FUNCTION_ERROR_INJECTION) \
    $(wildcard include/config/MITIGATION_RETPOLINE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/buildid.h \
    $(wildcard include/config/VMCORE_INFO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kmod.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/umh.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/elf.h \
    $(wildcard include/config/ARCH_HAVE_EXTRA_ELF_NOTES) \
    $(wildcard include/config/ARCH_USE_GNU_PROPERTY) \
    $(wildcard include/config/ARCH_HAVE_ELF_PROT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/elf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/user.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/elf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/elf-em.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/moduleparam.h \
    $(wildcard include/config/ALPHA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rbtree_latch.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/error-injection.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/error-injection.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dynamic_debug.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/module.h \
    $(wildcard include/config/ARM_UNWIND) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/module.h \
    $(wildcard include/config/HAVE_MOD_ARCH_SPECIFIC) \
    $(wildcard include/config/MODULES_USE_ELF_REL) \
    $(wildcard include/config/MODULES_USE_ELF_RELA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/unwind.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/device.h \
    $(wildcard include/config/ARM_DMA_USE_IOMMU) \
    $(wildcard include/config/ARCH_OMAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pm_wakeup.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pagevec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bio.h \
    $(wildcard include/config/BLK_DEV_ZONED) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mempool.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uio.h \
    $(wildcard include/config/ARCH_HAS_UACCESS_FLUSHCACHE) \
    $(wildcard include/config/ARCH_HAS_COPY_MC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/uio.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/node.h \
    $(wildcard include/config/HMEM_REPORTING) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pagemap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hugetlb_inline.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mempolicy.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/userfaultfd_k.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/swapops.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/swapfile.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/numa_balancing.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hugetlb.h \
    $(wildcard include/config/ARCH_ENABLE_HUGEPAGE_MIGRATION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mman.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mman.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/mman.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/system_info.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/mman.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/mman.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/mman-common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/hugetlb_encode.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ksm.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rmap.h \
    $(wildcard include/config/HAVE_GUP_FAST) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/delayacct.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pfn_t.h \
    $(wildcard include/config/FS_DAX_LIMITED) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmu_notifier.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/interval_tree.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/migrate.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mempolicy.h \
    $(wildcard include/config/TMPFS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/shmem_fs.h \
    $(wildcard include/config/TMPFS_QUOTA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/file.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/xattr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/xattr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/libc-compat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fs_parser.h \
    $(wildcard include/config/VALIDATE_FS_PARSER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fs_context.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/security.h \
    $(wildcard include/config/SECURITY_NETWORK) \
    $(wildcard include/config/SECURITY_INFINIBAND) \
    $(wildcard include/config/SECURITY_NETWORK_XFRM) \
    $(wildcard include/config/SECURITY_PATH) \
    $(wildcard include/config/SECURITYFS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kernel_read_file.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sockptr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpf.h \
    $(wildcard include/config/BPF_JIT) \
    $(wildcard include/config/FINEIBT) \
    $(wildcard include/config/BPF_JIT_ALWAYS_ON) \
    $(wildcard include/config/INET) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/bpf.h \
    $(wildcard include/config/BPF_LIRC_MODE2) \
    $(wildcard include/config/EFFICIENT_UNALIGNED_ACCESS) \
    $(wildcard include/config/IP_ROUTE_CLASSID) \
    $(wildcard include/config/BPF_KPROBE_OVERRIDE) \
    $(wildcard include/config/XFRM) \
    $(wildcard include/config/IPV6) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/bpf_common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/filter.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kallsyms.h \
    $(wildcard include/config/KALLSYMS_ALL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpfptr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/btf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bsearch.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/btf_ids.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/btf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcupdate_trace.h \
    $(wildcard include/config/TASKS_TRACE_RCU_READ_MB) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/static_call.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpu.h \
    $(wildcard include/config/GENERIC_CPU_DEVICES) \
    $(wildcard include/config/PM_SLEEP_SMP) \
    $(wildcard include/config/PM_SLEEP_SMP_NONZERO_CPU) \
    $(wildcard include/config/ARCH_HAS_CPU_FINALIZE_INIT) \
    $(wildcard include/config/CPU_MITIGATIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpuhotplug.h \
    $(wildcard include/config/HOTPLUG_CORE_SYNC_DEAD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpuhplock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpu_smt.h \
    $(wildcard include/config/HOTPLUG_SMT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cfi.h \
    $(wildcard include/config/CFI_CLANG) \
  arch/arm/include/generated/asm/cfi.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/cfi.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpf_types.h \
    $(wildcard include/config/NETFILTER_BPF_LINK) \
    $(wildcard include/config/XDP_SOCKETS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/lsm.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/unistd.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/unistd.h \
    $(wildcard include/config/OABI_COMPAT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/unistd.h \
  arch/arm/include/generated/uapi/asm/unistd-eabi.h \
  arch/arm/include/generated/asm/unistd-nr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/memory-tiers.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/debugfs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dax.h \
    $(wildcard include/config/DAX) \
    $(wildcard include/config/DEV_DAX_HMEM_DEVICES) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/oom.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/oom.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/perf_event.h \
    $(wildcard include/config/FUNCTION_TRACER) \
    $(wildcard include/config/GUEST_PERF_EVENTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/perf_event.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/bpf_perf_event.h \
  arch/arm/include/generated/uapi/asm/bpf_perf_event.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/bpf_perf_event.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ptrace.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pid_namespace.h \
    $(wildcard include/config/MEMFD_CREATE) \
    $(wildcard include/config/PID_NS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ptrace.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seccomp.h \
    $(wildcard include/config/HAVE_ARCH_SECCOMP_FILTER) \
    $(wildcard include/config/SECCOMP_FILTER) \
    $(wildcard include/config/CHECKPOINT_RESTORE) \
    $(wildcard include/config/SECCOMP_CACHE_DEBUG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/seccomp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/seccomp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/seccomp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/perf_event.h \
  arch/arm/include/generated/asm/local64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/local64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rhashtable-types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ftrace.h \
    $(wildcard include/config/HAVE_FUNCTION_GRAPH_FREGS) \
    $(wildcard include/config/DYNAMIC_FTRACE) \
    $(wildcard include/config/HAVE_DYNAMIC_FTRACE_WITH_ARGS) \
    $(wildcard include/config/HAVE_FTRACE_REGS_HAVING_PT_REGS) \
    $(wildcard include/config/DYNAMIC_FTRACE_WITH_REGS) \
    $(wildcard include/config/DYNAMIC_FTRACE_WITH_ARGS) \
    $(wildcard include/config/DYNAMIC_FTRACE_WITH_DIRECT_CALLS) \
    $(wildcard include/config/STACK_TRACER) \
    $(wildcard include/config/DYNAMIC_FTRACE_WITH_CALL_OPS) \
    $(wildcard include/config/FRAME_POINTER) \
    $(wildcard include/config/FUNCTION_GRAPH_RETVAL) \
    $(wildcard include/config/FUNCTION_PROFILER) \
    $(wildcard include/config/FTRACE_SYSCALLS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/trace_recursion.h \
    $(wildcard include/config/FTRACE_RECORD_RECURSION) \
    $(wildcard include/config/FTRACE_VALIDATE_RCU_IS_WATCHING) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/trace_clock.h \
  arch/arm/include/generated/asm/trace_clock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/trace_clock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/ftrace.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ftrace_regs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irq_work.h \
    $(wildcard include/config/IRQ_WORK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/irq_work.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/smp_plat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cpu.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cputype.h \
    $(wildcard include/config/CPU_CP15) \
    $(wildcard include/config/CPU_PJ4) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/jump_label_ratelimit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/perf_regs.h \
    $(wildcard include/config/HAVE_PERF_REGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/task_stack.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/magic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/perf_regs.h \
  arch/arm/include/generated/asm/local.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/local.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vmalloc.h \
    $(wildcard include/config/HAVE_ARCH_HUGE_VMALLOC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/vmalloc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/sysctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/events/kmem.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/tracepoint.h \
    $(wildcard include/config/HAVE_SYSCALL_TRACEPOINTS) \
    $(wildcard include/config/ARCH_WANTS_NO_INSTR) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/events/mmflags.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compaction.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/define_trace.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/mmu_context.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/mm_hooks.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/mmu_context.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/pgalloc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/pgalloc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/tlb.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/tlb.h \
    $(wildcard include/config/MMU_GATHER_TABLE_FREE) \
    $(wildcard include/config/MMU_GATHER_RCU_TABLE_FREE) \
    $(wildcard include/config/MMU_GATHER_HAVE_TABLE_FREE) \
    $(wildcard include/config/MMU_GATHER_NO_GATHER) \
    $(wildcard include/config/MMU_GATHER_PAGE_SIZE) \
    $(wildcard include/config/MMU_GATHER_NO_RANGE) \
    $(wildcard include/config/MMU_GATHER_NO_FLUSH_CACHE) \
    $(wildcard include/config/MMU_GATHER_MERGE_VMAS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/mm/pgalloc-track.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/mm/internal.h \
    $(wildcard include/config/DEBUG_MEMORY_INIT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/khugepaged.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/swap_cgroup.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/mm/vma.h \
    $(wildcard include/config/DEBUG_VM_MAPLE_TREE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/mm/swap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/extable.h \

mm/memory.o: $(deps_mm/memory.o)

$(deps_mm/memory.o):
#SYMVER max_mapnr 0x01139ffc
#SYMVER mem_map 0x785f6253
#SYMVER high_memory 0x8a7d1c31
#SYMVER zero_pfn 0x85efc7e0
#SYMVER zap_vma_ptes 0xb993ca8c
#SYMVER vm_insert_pages 0x659f2329
#SYMVER vm_insert_page 0x9d4c7358
#SYMVER vm_map_pages 0x0a455bc8
#SYMVER vm_map_pages_zero 0x25748e96
#SYMVER vmf_insert_pfn_prot 0xf70c3552
#SYMVER vmf_insert_pfn 0x7bac920a
#SYMVER vmf_insert_mixed 0x3141191f
#SYMVER remap_pfn_range 0x8518d374
#SYMVER vm_iomap_memory 0xb325eaf1
#SYMVER apply_to_page_range 0xb4f7af80
#SYMVER apply_to_existing_page_range 0x1a3b087d
#SYMVER unmap_mapping_pages 0x29e97826
#SYMVER unmap_mapping_range 0x3d6326e9
#SYMVER handle_mm_fault 0x3806438b
#SYMVER follow_pfnmap_start 0x70c822aa
#SYMVER follow_pfnmap_end 0xe50f4b3d
#SYMVER access_process_vm 0x70ad4708
