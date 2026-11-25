savedcmd_net/core/dev.o := clang -fintegrated-cc1 -Wp,-MMD,net/core/.dev.o.d -nostdinc -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include -I./arch/arm/include/generated -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include -I./include -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi -I./arch/arm/include/generated/uapi -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi -I./include/generated/uapi -include /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler-version.h -include /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kconfig.h -include /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compiler_types.h -D__KERNEL__ --target=arm-linux-gnueabi -fintegrated-as -Werror=unknown-warning-option -Werror=ignored-optimization-argument -Werror=option-ignored -Werror=unused-command-line-argument -mlittle-endian -D__LINUX_ARM_ARCH__=7 -fmacro-prefix-map=/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/= -std=gnu11 -fshort-wchar -funsigned-char -fno-common -fno-PIE -fno-strict-aliasing -fno-dwarf2-cfi-asm -mtp=cp15 -mabi=aapcs-linux -mfpu=vfp -funwind-tables -meabi gnu -Wa,-W -march=armv7-a -msoft-float -Uarm -fno-delete-null-pointer-checks -O2 -fstack-protector-strong -ftrivial-auto-var-init=zero -pg -fstrict-flex-arrays=3 -fno-strict-overflow -fno-stack-check -fno-builtin-wcslen -fno-builtin-wcslen -Wall -Wextra -Wundef -Werror=implicit-function-declaration -Werror=implicit-int -Werror=return-type -Werror=strict-prototypes -Wno-format-security -Wno-trigraphs -Wno-frame-address -Wno-address-of-packed-member -Wmissing-declarations -Wmissing-prototypes -Wframe-larger-than=1024 -Wno-gnu -Wno-format-overflow-non-kprintf -Wno-format-truncation-non-kprintf -Wno-default-const-init-unsafe -Wvla -Wno-pointer-sign -Wcast-function-type -Wno-unterminated-string-initialization -Wimplicit-fallthrough -Werror=date-time -Werror=incompatible-pointer-types -Wenum-conversion -Wunused -Wno-unused-but-set-variable -Wno-unused-const-variable -Wno-format-overflow -Wno-override-init -Wno-pointer-to-enum-cast -Wno-tautological-constant-out-of-range-compare -Wno-unaligned-access -Wno-enum-compare-conditional -Wno-missing-field-initializers -Wno-type-limits -Wno-shift-negative-value -Wno-enum-enum-conversion -Wno-sign-compare -Wno-unused-parameter -g -gdwarf-4  -fprofile-arcs -ftest-coverage  -fdebug-info-for-profiling -mllvm -enable-fs-discriminator=true -mllvm -improved-fs-discriminator=true -I/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/net/core -Inet/core    -DKBUILD_MODFILE='"net/core/dev"' -DKBUILD_BASENAME='"dev"' -DKBUILD_MODNAME='"dev"' -D__KBUILD_MODNAME=kmod_dev -c -o net/core/dev.o /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/net/core/dev.c  

source_net/core/dev.o := /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/net/core/dev.c

deps_net/core/dev.o := \
    $(wildcard include/config/PREEMPT_RT) \
    $(wildcard include/config/RPS) \
    $(wildcard include/config/LOCKDEP) \
    $(wildcard include/config/NET_INGRESS) \
    $(wildcard include/config/NET_EGRESS) \
    $(wildcard include/config/NET_CLS_ACT) \
    $(wildcard include/config/JUMP_LABEL) \
    $(wildcard include/config/XPS) \
    $(wildcard include/config/NUMA) \
    $(wildcard include/config/SYSFS) \
    $(wildcard include/config/BUG) \
    $(wildcard include/config/HIGHMEM) \
    $(wildcard include/config/NET_MPLS_GSO) \
    $(wildcard include/config/CGROUP_NET_PRIO) \
    $(wildcard include/config/NET_XGRESS) \
    $(wildcard include/config/RFS_ACCEL) \
    $(wildcard include/config/NET_FLOW_LIMIT) \
    $(wildcard include/config/BRIDGE) \
    $(wildcard include/config/ATM_LANE) \
    $(wildcard include/config/NET_RX_BUSY_POLL) \
    $(wildcard include/config/NETPOLL) \
    $(wildcard include/config/BQL) \
    $(wildcard include/config/PHYLIB) \
    $(wildcard include/config/PCPU_DEV_REFCNT) \
    $(wildcard include/config/NET_SCHED) \
    $(wildcard include/config/XFRM_OFFLOAD) \
    $(wildcard include/config/NETFILTER_EGRESS) \
    $(wildcard include/config/PAGE_POOL) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uaccess.h \
    $(wildcard include/config/PREEMPT_COUNT) \
    $(wildcard include/config/ARCH_HAS_SUBPAGE_FAULTS) \
    $(wildcard include/config/HARDENED_USERCOPY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fault-inject-usercopy.h \
    $(wildcard include/config/FAULT_INJECTION_USERCOPY) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/instrumented.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kmsan-checks.h \
    $(wildcard include/config/KMSAN) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/minmax.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/build_bug.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/const.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/const.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/const.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/nospec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/barrier.h \
    $(wildcard include/config/CPU_32v6K) \
    $(wildcard include/config/THUMB2_KERNEL) \
    $(wildcard include/config/CPU_XSC3) \
    $(wildcard include/config/CPU_FA526) \
    $(wildcard include/config/ARM_HEAVY_MB) \
    $(wildcard include/config/ARM_DMA_MEM_BUFFERABLE) \
    $(wildcard include/config/SMP) \
    $(wildcard include/config/CPU_SPECTRE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/barrier.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched.h \
    $(wildcard include/config/DEBUG_ATOMIC_SLEEP) \
    $(wildcard include/config/VIRT_CPU_ACCOUNTING_NATIVE) \
    $(wildcard include/config/SCHED_INFO) \
    $(wildcard include/config/SCHEDSTATS) \
    $(wildcard include/config/SCHED_CORE) \
    $(wildcard include/config/FAIR_GROUP_SCHED) \
    $(wildcard include/config/RT_GROUP_SCHED) \
    $(wildcard include/config/RT_MUTEXES) \
    $(wildcard include/config/UCLAMP_TASK) \
    $(wildcard include/config/UCLAMP_BUCKETS_COUNT) \
    $(wildcard include/config/KMAP_LOCAL) \
    $(wildcard include/config/THREAD_INFO_IN_TASK) \
    $(wildcard include/config/MEM_ALLOC_PROFILING) \
    $(wildcard include/config/SCHED_CLASS_EXT) \
    $(wildcard include/config/CGROUP_SCHED) \
    $(wildcard include/config/PREEMPT_NOTIFIERS) \
    $(wildcard include/config/BLK_DEV_IO_TRACE) \
    $(wildcard include/config/PREEMPT_RCU) \
    $(wildcard include/config/TASKS_RCU) \
    $(wildcard include/config/TASKS_TRACE_RCU) \
    $(wildcard include/config/MEMCG_V1) \
    $(wildcard include/config/LRU_GEN) \
    $(wildcard include/config/COMPAT_BRK) \
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
    $(wildcard include/config/VIRT_CPU_ACCOUNTING_GEN) \
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
    $(wildcard include/config/TRACE_IRQFLAGS) \
    $(wildcard include/config/UBSAN) \
    $(wildcard include/config/UBSAN_TRAP) \
    $(wildcard include/config/COMPACTION) \
    $(wildcard include/config/TASK_XACCT) \
    $(wildcard include/config/CPUSETS) \
    $(wildcard include/config/X86_CPU_RESCTRL) \
    $(wildcard include/config/FUTEX) \
    $(wildcard include/config/COMPAT) \
    $(wildcard include/config/PERF_EVENTS) \
    $(wildcard include/config/DEBUG_PREEMPT) \
    $(wildcard include/config/NUMA_BALANCING) \
    $(wildcard include/config/RSEQ) \
    $(wildcard include/config/SCHED_MM_CID) \
    $(wildcard include/config/FAULT_INJECTION) \
    $(wildcard include/config/LATENCYTOP) \
    $(wildcard include/config/KUNIT) \
    $(wildcard include/config/FUNCTION_GRAPH_TRACER) \
    $(wildcard include/config/TRACING) \
    $(wildcard include/config/KCOV) \
    $(wildcard include/config/MEMCG) \
    $(wildcard include/config/UPROBES) \
    $(wildcard include/config/BCACHE) \
    $(wildcard include/config/MMU) \
    $(wildcard include/config/VMAP_STACK) \
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
    $(wildcard include/config/PREEMPTION) \
    $(wildcard include/config/PREEMPT_DYNAMIC) \
    $(wildcard include/config/HAVE_PREEMPT_DYNAMIC_CALL) \
    $(wildcard include/config/HAVE_PREEMPT_DYNAMIC_KEY) \
    $(wildcard include/config/MEM_ALLOC_PROFILING_DEBUG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sched.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/current.h \
    $(wildcard include/config/CURRENT_POINTER_IN_TPIDRURO) \
    $(wildcard include/config/CPU_V6) \
    $(wildcard include/config/ARM_HAS_GROUP_RELOCS) \
    $(wildcard include/config/ARM_MODULE_PLTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/insn.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/processor.h \
    $(wildcard include/config/HAVE_HW_BREAKPOINT) \
    $(wildcard include/config/BINFMT_ELF_FDPIC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/hw_breakpoint.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/ptrace.h \
    $(wildcard include/config/ARM_THUMB) \
    $(wildcard include/config/CPU_V7M) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/unified.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/vdso/processor.h \
    $(wildcard include/config/ARM_ERRATA_754327) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/thread_info.h \
    $(wildcard include/config/GENERIC_ENTRY) \
    $(wildcard include/config/HAVE_ARCH_WITHIN_STACK_FRAMES) \
    $(wildcard include/config/SH) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/limits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/limits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/limits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bug.h \
    $(wildcard include/config/GENERIC_BUG) \
    $(wildcard include/config/BUG_ON_DATA_CORRUPTION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/bug.h \
    $(wildcard include/config/DEBUG_BUGVERBOSE) \
    $(wildcard include/config/ARM_LPAE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/linkage.h \
    $(wildcard include/config/ARCH_USE_SYM_ANNOTATIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stringify.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/export.h \
    $(wildcard include/config/MODVERSIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/linkage.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/opcodes.h \
    $(wildcard include/config/CPU_ENDIAN_BE32) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bug.h \
    $(wildcard include/config/GENERIC_BUG_RELATIVE_POINTERS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/instrumentation.h \
    $(wildcard include/config/NOINSTR_VALIDATION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/once_lite.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stdarg.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/init.h \
    $(wildcard include/config/MEMORY_HOTPLUG) \
    $(wildcard include/config/HAVE_ARCH_PREL32_RELOCATIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kern_levels.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ratelimit_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/bits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/bits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/overflow.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/restart_block.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/errno.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/errno.h \
  arch/arm/include/generated/uapi/asm/errno.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/errno.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/errno-base.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bitops.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/typecheck.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/kernel.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sysinfo.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/generic-non-atomic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/bitops.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqflags.h \
    $(wildcard include/config/PROVE_LOCKING) \
    $(wildcard include/config/IRQSOFF_TRACER) \
    $(wildcard include/config/PREEMPT_TRACER) \
    $(wildcard include/config/DEBUG_IRQFLAGS) \
    $(wildcard include/config/TRACE_IRQFLAGS_SUPPORT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqflags_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cleanup.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/irqflags.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/irqflags.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/percpu.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/prefetch.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/instrumented-lock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/le.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/bitops/ext2-atomic-setbit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/thread_info.h \
    $(wildcard include/config/KASAN) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/log2.h \
    $(wildcard include/config/ARCH_HAS_ILOG2_U32) \
    $(wildcard include/config/ARCH_HAS_ILOG2_U64) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/memory_model.h \
    $(wildcard include/config/FLATMEM) \
    $(wildcard include/config/SPARSEMEM_VMEMMAP) \
    $(wildcard include/config/SPARSEMEM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pfn.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/traps.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/list.h \
    $(wildcard include/config/LIST_HARDENED) \
    $(wildcard include/config/DEBUG_LIST) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/container_of.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/poison.h \
    $(wildcard include/config/ILLEGAL_POINTER_VALUE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/preempt.h \
    $(wildcard include/config/TRACE_PREEMPT_TOGGLE) \
    $(wildcard include/config/PREEMPT_NONE) \
    $(wildcard include/config/PREEMPT_VOLUNTARY) \
    $(wildcard include/config/PREEMPT) \
  arch/arm/include/generated/asm/preempt.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/preempt.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpumask_types.h \
    $(wildcard include/config/CPUMASK_OFFSTACK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cache.h \
    $(wildcard include/config/ARCH_HAS_CACHE_LINE_SIZE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/smp_types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/llist.h \
    $(wildcard include/config/ARCH_HAVE_NMI_SAFE_CMPXCHG) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/numa.h \
    $(wildcard include/config/NODES_SHIFT) \
    $(wildcard include/config/NUMA_KEEP_MEMINFO) \
    $(wildcard include/config/HAVE_ARCH_NODE_DEV_GROUP) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/jump_label.h \
    $(wildcard include/config/HAVE_ARCH_JUMP_LABEL_RELATIVE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/jump_label.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/static_call_types.h \
    $(wildcard include/config/HAVE_STATIC_CALL) \
    $(wildcard include/config/HAVE_STATIC_CALL_INLINE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uidgid_types.h \
  arch/arm/include/generated/asm/kmap_size.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/kmap_size.h \
    $(wildcard include/config/DEBUG_KMAP_LOCAL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/ext.h \
    $(wildcard include/config/EXT_GROUP_SCHED) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/spinlock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bottom_half.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/instruction_pointer.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/lockdep.h \
    $(wildcard include/config/DEBUG_LOCKING_API_SELFTESTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/smp.h \
    $(wildcard include/config/UP_LATE_INIT) \
    $(wildcard include/config/CSD_LOCK_WAIT_DEBUG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpumask.h \
    $(wildcard include/config/FORCE_NR_CPUS) \
    $(wildcard include/config/HOTPLUG_CPU) \
    $(wildcard include/config/DEBUG_PER_CPU_MAPS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kernel.h \
    $(wildcard include/config/PREEMPT_VOLUNTARY_BUILD) \
    $(wildcard include/config/PREEMPT_) \
    $(wildcard include/config/FTRACE_MCOUNT_RECORD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/align.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/array_size.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hex.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kstrtox.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/math.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/div64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/compiler.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/div64.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sprintf.h \
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
    $(wildcard include/config/BCM2835_FAST_MEMCPY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bitmap-str.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/gfp_types.h \
    $(wildcard include/config/KASAN_HW_TAGS) \
    $(wildcard include/config/SLAB_OBJ_EXT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/smp.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/uaccess.h \
    $(wildcard include/config/CPU_SW_DOMAIN_PAN) \
    $(wildcard include/config/CPU_TTBR0_PAN) \
    $(wildcard include/config/HAVE_EFFICIENT_UNALIGNED_ACCESS) \
    $(wildcard include/config/UACCESS_WITH_MEMCPY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/domain.h \
    $(wildcard include/config/IO_36) \
    $(wildcard include/config/CPU_USE_DOMAINS) \
    $(wildcard include/config/CPU_CP15_MMU) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/unaligned.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/unaligned/packed_struct.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/unaligned.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mm_types.h \
    $(wildcard include/config/HAVE_ALIGNED_STRUCT_PAGE) \
    $(wildcard include/config/HUGETLB_PMD_PAGE_TABLE_SHARING) \
    $(wildcard include/config/USERFAULTFD) \
    $(wildcard include/config/ANON_VMA_NAME) \
    $(wildcard include/config/PER_VMA_LOCK) \
    $(wildcard include/config/SWAP) \
    $(wildcard include/config/HAVE_ARCH_COMPAT_MMAP_BASES) \
    $(wildcard include/config/MEMBARRIER) \
    $(wildcard include/config/AIO) \
    $(wildcard include/config/MMU_NOTIFIER) \
    $(wildcard include/config/TRANSPARENT_HUGEPAGE) \
    $(wildcard include/config/SPLIT_PMD_PTLOCKS) \
    $(wildcard include/config/HUGETLB_PAGE) \
    $(wildcard include/config/IOMMU_MM_DATA) \
    $(wildcard include/config/KSM) \
    $(wildcard include/config/LRU_GEN_WALKS_MMU) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/context_tracking_irq.h \
    $(wildcard include/config/CONTEXT_TRACKING_IDLE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcutree.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/maple_tree.h \
    $(wildcard include/config/MAPLE_RCU_DISABLED) \
    $(wildcard include/config/DEBUG_MAPLE_TREE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rwsem.h \
    $(wildcard include/config/RWSEM_SPIN_ON_OWNER) \
    $(wildcard include/config/DEBUG_RWSEMS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/completion.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/swait.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/wait.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uprobes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/uprobes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/probes.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page-flags-layout.h \
  include/generated/bounds.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/workqueue.h \
    $(wildcard include/config/DEBUG_OBJECTS_WORK) \
    $(wildcard include/config/FREEZER) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seqlock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mutex.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/debug_locks.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu_counter.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu.h \
    $(wildcard include/config/MODULES) \
    $(wildcard include/config/RANDOM_KMALLOC_CACHES) \
    $(wildcard include/config/PAGE_SIZE_4KB) \
    $(wildcard include/config/NEED_PER_CPU_PAGE_FIRST_CHUNK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/alloc_tag.h \
    $(wildcard include/config/MEM_ALLOC_PROFILING_ENABLED_BY_DEFAULT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/codetag.h \
    $(wildcard include/config/CODE_TAGGING) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/static_key.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmdebug.h \
    $(wildcard include/config/DEBUG_VM) \
    $(wildcard include/config/DEBUG_VM_IRQSOFF) \
    $(wildcard include/config/DEBUG_VM_PGFLAGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/mmu.h \
    $(wildcard include/config/CPU_HAS_ASID) \
    $(wildcard include/config/VDSO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/pgtable-3level.h \
  arch/arm/include/generated/asm/extable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/extable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/access_ok.h \
    $(wildcard include/config/ALTERNATE_USER_ADDRESS_SPACE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/capability.h \
    $(wildcard include/config/MULTIUSER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/capability.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uidgid.h \
    $(wildcard include/config/USER_NS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/highuid.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpu.h \
    $(wildcard include/config/GENERIC_CPU_DEVICES) \
    $(wildcard include/config/PM_SLEEP_SMP) \
    $(wildcard include/config/PM_SLEEP_SMP_NONZERO_CPU) \
    $(wildcard include/config/ARCH_HAS_CPU_FINALIZE_INIT) \
    $(wildcard include/config/CPU_MITIGATIONS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/node.h \
    $(wildcard include/config/HMEM_REPORTING) \
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
    $(wildcard include/config/PM_SLEEP) \
    $(wildcard include/config/OF) \
    $(wildcard include/config/DEVTMPFS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dev_printk.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ratelimit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/energy_model.h \
    $(wildcard include/config/SCHED_DEBUG) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/gfp.h \
    $(wildcard include/config/ZONE_DMA) \
    $(wildcard include/config/ZONE_DMA32) \
    $(wildcard include/config/ZONE_DEVICE) \
    $(wildcard include/config/CONTIG_ALLOC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmzone.h \
    $(wildcard include/config/ARCH_FORCE_MAX_ORDER) \
    $(wildcard include/config/CMA) \
    $(wildcard include/config/MEMORY_ISOLATION) \
    $(wildcard include/config/ZSMALLOC) \
    $(wildcard include/config/UNACCEPTED_MEMORY) \
    $(wildcard include/config/SHADOW_CALL_STACK) \
    $(wildcard include/config/IOMMU_SUPPORT) \
    $(wildcard include/config/LRU_GEN_STATS) \
    $(wildcard include/config/MEMORY_FAILURE) \
    $(wildcard include/config/PAGE_EXTENSION) \
    $(wildcard include/config/DEFERRED_STRUCT_PAGE_INIT) \
    $(wildcard include/config/HAVE_MEMORYLESS_NODES) \
    $(wildcard include/config/SPARSEMEM_EXTREME) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/list_nulls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/nodemask.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/random.h \
    $(wildcard include/config/VMGENID) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/random.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ioctl.h \
  arch/arm/include/generated/uapi/asm/ioctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/ioctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/ioctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqnr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/irqnr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/prandom.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/once.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pageblock-flags.h \
    $(wildcard include/config/HUGETLB_PAGE_SIZE_VARIABLE) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/topology.h \
    $(wildcard include/config/USE_PERCPU_NUMA_NODE_ID) \
    $(wildcard include/config/SCHED_SMT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/arch_topology.h \
    $(wildcard include/config/GENERIC_ARCH_TOPOLOGY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/topology.h \
    $(wildcard include/config/ARM_CPU_TOPOLOGY) \
    $(wildcard include/config/BL_SWITCHER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/topology.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/mm.h \
    $(wildcard include/config/MMU_LAZY_TLB_REFCOUNT) \
    $(wildcard include/config/ARCH_HAS_MEMBARRIER_CALLBACKS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sync_core.h \
    $(wildcard include/config/ARCH_HAS_SYNC_CORE_BEFORE_USERMODE) \
    $(wildcard include/config/ARCH_HAS_PREPARE_SYNC_CORE_CMD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/coredump.h \
    $(wildcard include/config/CORE_DUMP_DEFAULT_ELF_HEADERS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kobject_ns.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/stat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/stat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/cpufreq.h \
    $(wildcard include/config/CPU_FREQ) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/topology.h \
    $(wildcard include/config/SCHED_CLUSTER) \
    $(wildcard include/config/SCHED_MC) \
    $(wildcard include/config/CPU_FREQ_GOV_SCHEDUTIL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/idle.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/sd_flags.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ioport.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/klist.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pm.h \
    $(wildcard include/config/VT_CONSOLE_SLEEP) \
    $(wildcard include/config/CXL_SUSPEND) \
    $(wildcard include/config/PM_CLK) \
    $(wildcard include/config/PM_GENERIC_DOMAINS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hrtimer.h \
    $(wildcard include/config/HIGH_RES_TIMERS) \
    $(wildcard include/config/TIME_LOW_RES) \
    $(wildcard include/config/TIMERFD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hrtimer_defs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/timerqueue.h \
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
    $(wildcard include/config/TRACEPOINTS) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sysctl.h \
    $(wildcard include/config/SYSCTL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sysctl.h \
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
    $(wildcard include/config/PPC64) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rbtree_latch.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/error-injection.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/error-injection.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/tracepoint-defs.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpuhotplug.h \
    $(wildcard include/config/HOTPLUG_CORE_SYNC_DEAD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpuhplock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpu_smt.h \
    $(wildcard include/config/HOTPLUG_SMT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hash.h \
    $(wildcard include/config/HAVE_ARCH_HASH) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/slab.h \
    $(wildcard include/config/FAILSLAB) \
    $(wildcard include/config/KFENCE) \
    $(wildcard include/config/SLUB_TINY) \
    $(wildcard include/config/SLUB_DEBUG) \
    $(wildcard include/config/SLAB_FREELIST_HARDENED) \
    $(wildcard include/config/SLAB_BUCKETS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/percpu-refcount.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kasan.h \
    $(wildcard include/config/KASAN_STACK) \
    $(wildcard include/config/KASAN_VMALLOC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kasan-enabled.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kasan-tags.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/isolation.h \
    $(wildcard include/config/CPU_ISOLATION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpuset.h \
    $(wildcard include/config/CPUSETS_V1) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/task.h \
    $(wildcard include/config/HAVE_EXIT_THREAD) \
    $(wildcard include/config/ARCH_WANTS_DYNAMIC_TASK_STRUCT) \
    $(wildcard include/config/HAVE_ARCH_THREAD_STRUCT_WHITELIST) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mm.h \
    $(wildcard include/config/HAVE_ARCH_MMAP_RND_BITS) \
    $(wildcard include/config/HAVE_ARCH_MMAP_RND_COMPAT_BITS) \
    $(wildcard include/config/MEM_SOFT_DIRTY) \
    $(wildcard include/config/ARCH_USES_HIGH_VMA_FLAGS) \
    $(wildcard include/config/ARCH_HAS_PKEYS) \
    $(wildcard include/config/ARCH_PKEY_BITS) \
    $(wildcard include/config/X86_USER_SHADOW_STACK) \
    $(wildcard include/config/X86) \
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
    $(wildcard include/config/ARCH_HAS_PTE_SPECIAL) \
    $(wildcard include/config/ARCH_SUPPORTS_PMD_PFNMAP) \
    $(wildcard include/config/ARCH_SUPPORTS_PUD_PFNMAP) \
    $(wildcard include/config/ARCH_HAS_PTE_DEVMAP) \
    $(wildcard include/config/SPLIT_PTE_PTLOCKS) \
    $(wildcard include/config/HIGHPTE) \
    $(wildcard include/config/DEBUG_VM_RB) \
    $(wildcard include/config/PAGE_POISONING) \
    $(wildcard include/config/INIT_ON_ALLOC_DEFAULT_ON) \
    $(wildcard include/config/INIT_ON_FREE_DEFAULT_ON) \
    $(wildcard include/config/DEBUG_PAGEALLOC) \
    $(wildcard include/config/ARCH_WANT_OPTIMIZE_DAX_VMEMMAP) \
    $(wildcard include/config/HUGETLBFS) \
    $(wildcard include/config/MAPPING_DIRTY_HELPERS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pgalloc_tag.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmap_lock.h \
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
    $(wildcard include/config/HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD) \
    $(wildcard include/config/HAVE_ARCH_SOFT_DIRTY) \
    $(wildcard include/config/ARCH_ENABLE_THP_MIGRATION) \
    $(wildcard include/config/HAVE_ARCH_HUGE_VMAP) \
    $(wildcard include/config/X86_ESPFIX64) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/pgtable_uffd.h \
    $(wildcard include/config/HAVE_ARCH_USERFAULTFD_WP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page_table_check.h \
    $(wildcard include/config/PAGE_TABLE_CHECK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/memremap.h \
    $(wildcard include/config/DEVICE_PRIVATE) \
    $(wildcard include/config/PCI_P2PDMA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/huge_mm.h \
    $(wildcard include/config/PGTABLE_HAS_HUGE_LEAVES) \
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
    $(wildcard include/config/PROC_FS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/jobctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cred.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/key.h \
    $(wildcard include/config/KEY_NOTIFICATIONS) \
    $(wildcard include/config/NET) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/assoc_array.h \
    $(wildcard include/config/ASSOCIATIVE_ARRAY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/user.h \
    $(wildcard include/config/VFIO_PCI_ZDEV_KVM) \
    $(wildcard include/config/IOMMUFD) \
    $(wildcard include/config/WATCH_QUEUE) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mmu_context.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/mmu_context.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/smp_plat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cpu.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/cputype.h \
    $(wildcard include/config/CPU_CP15) \
    $(wildcard include/config/CPU_PJ4) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/mm_hooks.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/mmu_context.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/tick.h \
    $(wildcard include/config/GENERIC_CLOCKEVENTS) \
    $(wildcard include/config/SUSPEND) \
    $(wildcard include/config/TICK_ONESHOT) \
    $(wildcard include/config/GENERIC_CLOCKEVENTS_BROADCAST) \
    $(wildcard include/config/NO_HZ_COMMON) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/clockchips.h \
    $(wildcard include/config/ARCH_HAS_TICK_BROADCAST) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/clocksource.h \
    $(wildcard include/config/ARCH_CLOCKSOURCE_DATA) \
    $(wildcard include/config/GENERIC_GETTIMEOFDAY) \
    $(wildcard include/config/CLOCKSOURCE_WATCHDOG) \
    $(wildcard include/config/ARCH_CLOCKSOURCE_INIT) \
    $(wildcard include/config/TIMER_PROBE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/of.h \
    $(wildcard include/config/OF_DYNAMIC) \
    $(wildcard include/config/SPARC) \
    $(wildcard include/config/OF_PROMTREE) \
    $(wildcard include/config/OF_KOBJ) \
    $(wildcard include/config/OF_NUMA) \
    $(wildcard include/config/OF_OVERLAY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mod_devicetable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mei.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mei_uuid.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/property.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/fwnode.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/io.h \
    $(wildcard include/config/PCI) \
    $(wildcard include/config/PCMCIA) \
    $(wildcard include/config/NEED_MACH_IO_H) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/pci_iomap.h \
    $(wildcard include/config/NO_GENERIC_PCI_IOPORT_MAP) \
    $(wildcard include/config/HAS_IOPORT_MAP) \
    $(wildcard include/config/GENERIC_PCI_IOMAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/io.h \
    $(wildcard include/config/GENERIC_IOMAP) \
    $(wildcard include/config/TRACE_MMIO_ACCESS) \
    $(wildcard include/config/GENERIC_IOREMAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/logic_pio.h \
    $(wildcard include/config/INDIRECT_PIO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/clocksource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/vdso/clocksource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/vdso/clocksource.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/context_tracking_state.h \
    $(wildcard include/config/CONTEXT_TRACKING_USER) \
    $(wildcard include/config/CONTEXT_TRACKING) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/smpboot.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/socket.h \
  arch/arm/include/generated/uapi/asm/socket.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/socket.h \
  arch/arm/include/generated/uapi/asm/sockios.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/sockios.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sockios.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/uio.h \
    $(wildcard include/config/ARCH_HAS_UACCESS_FLUSHCACHE) \
    $(wildcard include/config/ARCH_HAS_COPY_MC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/uio.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/socket.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/interrupt.h \
    $(wildcard include/config/IRQ_FORCED_THREADING) \
    $(wildcard include/config/GENERIC_IRQ_PROBE) \
    $(wildcard include/config/IRQ_TIMINGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqreturn.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hardirq.h \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/io.h \
  arch/arm/include/generated/asm/irq_regs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/irq_regs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/irqdesc.h \
    $(wildcard include/config/GENERIC_IRQ_STAT_SNAPSHOT) \
    $(wildcard include/config/GENERIC_IRQ_DEBUGFS) \
    $(wildcard include/config/IRQ_DOMAIN) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/hw_irq.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/sections.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/sections.h \
    $(wildcard include/config/HAVE_FUNCTION_DESCRIPTORS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/if_ether.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/skbuff.h \
    $(wildcard include/config/NF_CONNTRACK) \
    $(wildcard include/config/BRIDGE_NETFILTER) \
    $(wildcard include/config/NET_TC_SKB_EXT) \
    $(wildcard include/config/MAX_SKB_FRAGS) \
    $(wildcard include/config/NET_SOCK_MSG) \
    $(wildcard include/config/SKB_EXTENSIONS) \
    $(wildcard include/config/WIRELESS) \
    $(wildcard include/config/IPV6_NDISC_NODETYPE) \
    $(wildcard include/config/IP_VS) \
    $(wildcard include/config/NETFILTER_XT_TARGET_TRACE) \
    $(wildcard include/config/NF_TABLES) \
    $(wildcard include/config/NET_SWITCHDEV) \
    $(wildcard include/config/NET_REDIRECT) \
    $(wildcard include/config/NETFILTER_SKIP_EGRESS) \
    $(wildcard include/config/SKB_DECRYPTED) \
    $(wildcard include/config/IP_SCTP) \
    $(wildcard include/config/NETWORK_SECMARK) \
    $(wildcard include/config/DEBUG_NET) \
    $(wildcard include/config/NETWORK_PHY_TIMESTAMPING) \
    $(wildcard include/config/XFRM) \
    $(wildcard include/config/MPTCP) \
    $(wildcard include/config/MCTP_FLOWS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bvec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/highmem.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cacheflush.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kmsan.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dma-direction.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/highmem-internal.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/highmem.h \
    $(wildcard include/config/DEBUG_HIGHMEM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/fixmap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/fixmap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/checksum.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/checksum.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/in6.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/in6.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/libc-compat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dma-mapping.h \
    $(wildcard include/config/DMA_API_DEBUG) \
    $(wildcard include/config/HAS_DMA) \
    $(wildcard include/config/NEED_DMA_MAP_STATE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/scatterlist.h \
    $(wildcard include/config/NEED_SG_DMA_LENGTH) \
    $(wildcard include/config/NEED_SG_DMA_FLAGS) \
    $(wildcard include/config/DEBUG_SG) \
    $(wildcard include/config/SGL_ALLOC) \
    $(wildcard include/config/ARCH_NO_SG_CHAIN) \
    $(wildcard include/config/SG_POOL) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mem_encrypt.h \
    $(wildcard include/config/ARCH_HAS_MEM_ENCRYPT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netdev_features.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/flow_dissector.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/siphash.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_ether.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/pkt_cls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/pkt_sched.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_packet.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/flow.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter/nf_conntrack_common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netfilter/nf_conntrack_common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/net_debug.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/dropreason-core.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netmem.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netdevice.h \
    $(wildcard include/config/DCB) \
    $(wildcard include/config/HYPERV_NET) \
    $(wildcard include/config/WLAN) \
    $(wildcard include/config/AX25) \
    $(wildcard include/config/MAC80211_MESH) \
    $(wildcard include/config/NET_IPIP) \
    $(wildcard include/config/NET_IPGRE) \
    $(wildcard include/config/IPV6_SIT) \
    $(wildcard include/config/IPV6_TUNNEL) \
    $(wildcard include/config/XDP_SOCKETS) \
    $(wildcard include/config/FCOE) \
    $(wildcard include/config/NET_POLL_CONTROLLER) \
    $(wildcard include/config/LIBFCOE) \
    $(wildcard include/config/WIRELESS_EXT) \
    $(wildcard include/config/NET_L3_MASTER_DEV) \
    $(wildcard include/config/IPV6) \
    $(wildcard include/config/TLS_DEVICE) \
    $(wildcard include/config/VLAN_8021Q) \
    $(wildcard include/config/NET_DSA) \
    $(wildcard include/config/TIPC) \
    $(wildcard include/config/ATALK) \
    $(wildcard include/config/CFG80211) \
    $(wildcard include/config/IEEE802154) \
    $(wildcard include/config/6LOWPAN) \
    $(wildcard include/config/MPLS_ROUTING) \
    $(wildcard include/config/MCTP) \
    $(wildcard include/config/NETFILTER_INGRESS) \
    $(wildcard include/config/GARP) \
    $(wildcard include/config/MRP) \
    $(wildcard include/config/NET_DROP_MONITOR) \
    $(wildcard include/config/MACSEC) \
    $(wildcard include/config/DPLL) \
    $(wildcard include/config/DIMLIB) \
    $(wildcard include/config/NET_DEV_REFCNT_TRACKER) \
    $(wildcard include/config/ETHTOOL_NETLINK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/delay.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/delay.h \
  arch/arm/include/generated/asm/local.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/local.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dynamic_queue_limits.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/net_namespace.h \
    $(wildcard include/config/NF_FLOW_TABLE) \
    $(wildcard include/config/UNIX) \
    $(wildcard include/config/IEEE802154_6LOWPAN) \
    $(wildcard include/config/NETFILTER) \
    $(wildcard include/config/WEXT_CORE) \
    $(wildcard include/config/MPLS) \
    $(wildcard include/config/CAN) \
    $(wildcard include/config/CRYPTO_USER) \
    $(wildcard include/config/SMC) \
    $(wildcard include/config/NET_NS) \
    $(wildcard include/config/NET_NS_REFCNT_TRACKER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/core.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/mib.h \
    $(wildcard include/config/XFRM_STATISTICS) \
    $(wildcard include/config/TLS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/snmp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/snmp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/u64_stats_sync.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/unix.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/packet.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/ipv4.h \
    $(wildcard include/config/IP_ROUTE_MULTIPATH) \
    $(wildcard include/config/IP_MULTIPLE_TABLES) \
    $(wildcard include/config/IP_ROUTE_CLASSID) \
    $(wildcard include/config/IP_MROUTE) \
    $(wildcard include/config/IP_MROUTE_MULTIPLE_TABLES) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/inet_frag.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rhashtable-types.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/ipv6.h \
    $(wildcard include/config/IPV6_MULTIPLE_TABLES) \
    $(wildcard include/config/IPV6_SUBTREES) \
    $(wildcard include/config/IPV6_MROUTE) \
    $(wildcard include/config/IPV6_MROUTE_MULTIPLE_TABLES) \
    $(wildcard include/config/NF_DEFRAG_IPV6) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/dst_ops.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/icmpv6.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/nexthop.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/ieee802154_6lowpan.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/sctp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/netfilter.h \
    $(wildcard include/config/LWTUNNEL) \
    $(wildcard include/config/NETFILTER_FAMILY_ARP) \
    $(wildcard include/config/NETFILTER_FAMILY_BRIDGE) \
    $(wildcard include/config/NF_DEFRAG_IPV4) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter_defs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netfilter.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/in.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/in.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/conntrack.h \
    $(wildcard include/config/NF_CT_PROTO_DCCP) \
    $(wildcard include/config/NF_CT_PROTO_SCTP) \
    $(wildcard include/config/NF_CT_PROTO_GRE) \
    $(wildcard include/config/NF_CONNTRACK_EVENTS) \
    $(wildcard include/config/NF_CONNTRACK_LABELS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter/nf_conntrack_tcp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netfilter/nf_conntrack_tcp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter/nf_conntrack_dccp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netfilter/nf_conntrack_tuple_common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter/nf_conntrack_sctp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netfilter/nf_conntrack_sctp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/nftables.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/xfrm.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/xfrm.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/mpls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/can.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/xdp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/smc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/bpf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/mctp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/net_trackers.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ref_tracker.h \
    $(wildcard include/config/REF_TRACKER) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/stackdepot.h \
    $(wildcard include/config/STACKDEPOT) \
    $(wildcard include/config/STACKDEPOT_MAX_FRAMES) \
    $(wildcard include/config/STACKDEPOT_ALWAYS_INIT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ns_common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seq_file_net.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/seq_file.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/string_helpers.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ctype.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/string_choices.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netprio_cgroup.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cgroup.h \
    $(wildcard include/config/DEBUG_CGROUP_REF) \
    $(wildcard include/config/CGROUP_CPUACCT) \
    $(wildcard include/config/SOCK_CGROUP_DATA) \
    $(wildcard include/config/CGROUP_DATA) \
    $(wildcard include/config/CGROUP_BPF) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/cgroupstats.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/taskstats.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/nsproxy.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/user_namespace.h \
    $(wildcard include/config/INOTIFY_USER) \
    $(wildcard include/config/FANOTIFY) \
    $(wildcard include/config/BINFMT_MISC) \
    $(wildcard include/config/PERSISTENT_KEYRINGS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kernel_stat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cgroup-defs.h \
    $(wildcard include/config/CGROUP_NET_CLASSID) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/neighbour.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netlink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/scm.h \
    $(wildcard include/config/SECURITY_NETWORK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/net.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sockptr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/net.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/file.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/security.h \
    $(wildcard include/config/SECURITY_INFINIBAND) \
    $(wildcard include/config/SECURITY_NETWORK_XFRM) \
    $(wildcard include/config/SECURITY_PATH) \
    $(wildcard include/config/SECURITYFS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kernel_read_file.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpf.h \
    $(wildcard include/config/BPF_JIT) \
    $(wildcard include/config/FINEIBT) \
    $(wildcard include/config/BPF_JIT_ALWAYS_ON) \
    $(wildcard include/config/INET) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/bpf.h \
    $(wildcard include/config/BPF_LIRC_MODE2) \
    $(wildcard include/config/EFFICIENT_UNALIGNED_ACCESS) \
    $(wildcard include/config/BPF_KPROBE_OVERRIDE) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/memcontrol.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/page_counter.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vmpressure.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/eventfd.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/eventfd.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/writeback.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/flex_proportions.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/backing-dev-defs.h \
    $(wildcard include/config/DEBUG_FS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/blk_types.h \
    $(wildcard include/config/FAIL_MAKE_REQUEST) \
    $(wildcard include/config/BLK_CGROUP_IOCOST) \
    $(wildcard include/config/BLK_INLINE_ENCRYPTION) \
    $(wildcard include/config/BLK_DEV_INTEGRITY) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pagevec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bio.h \
    $(wildcard include/config/BLK_DEV_ZONED) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mempool.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cfi.h \
    $(wildcard include/config/CFI_CLANG) \
  arch/arm/include/generated/asm/cfi.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/cfi.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpf_types.h \
    $(wildcard include/config/NETFILTER_BPF_LINK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/lsm.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/unistd.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/unistd.h \
    $(wildcard include/config/OABI_COMPAT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/uapi/asm/unistd.h \
  arch/arm/include/generated/uapi/asm/unistd-eabi.h \
  arch/arm/include/generated/asm/unistd-nr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/compat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/compat.h \
    $(wildcard include/config/ARCH_HAS_SYSCALL_WRAPPER) \
    $(wildcard include/config/X86_X32_ABI) \
    $(wildcard include/config/COMPAT_OLD_SIGACTION) \
    $(wildcard include/config/ODD_RT_SIGACTION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sem.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sem.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ipc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ipc.h \
  arch/arm/include/generated/uapi/asm/ipcbuf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/ipcbuf.h \
  arch/arm/include/generated/uapi/asm/sembuf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/sembuf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/hdlc/ioctl.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/aio_abi.h \
  arch/arm/include/generated/asm/compat.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/asm-generic/compat.h \
    $(wildcard include/config/COMPAT_FOR_U64_ALIGNMENT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netlink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netdevice.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/if_link.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_link.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_bonding.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netdev.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/hashtable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/etherdevice.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/crc32.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bitrev.h \
    $(wildcard include/config/HAVE_ARCH_BITREVERSE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/bitrev.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ethtool.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ethtool.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/net_tstamp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpf_trace.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/events/xdp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/filter.h \
    $(wildcard include/config/HAVE_EBPF_JIT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/clock.h \
    $(wildcard include/config/ARCH_WANTS_NO_INSTR) \
    $(wildcard include/config/GENERIC_SCHED_CLOCK) \
    $(wildcard include/config/HAVE_UNSTABLE_SCHED_CLOCK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/set_memory.h \
    $(wildcard include/config/ARCH_HAS_SET_MEMORY) \
    $(wildcard include/config/ARCH_HAS_SET_DIRECT_MAP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/set_memory.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/if_vlan.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rtnetlink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/rtnetlink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_addr.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_vlan.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vmalloc.h \
    $(wildcard include/config/HAVE_ARCH_HUGE_VMALLOC) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/vmalloc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/crypto/sha1.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/sch_generic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/gen_stats.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/gen_stats.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/rtnetlink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netlink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/flow_offload.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/tracepoint.h \
    $(wildcard include/config/HAVE_SYSCALL_TRACEPOINTS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/xdp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/xdp_priv.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rhashtable.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/jhash.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/define_trace.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/sock.h \
    $(wildcard include/config/SOCK_RX_QUEUE_MAPPING) \
    $(wildcard include/config/SOCK_VALIDATE_XMIT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rculist_nulls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/poll.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/poll.h \
  arch/arm/include/generated/uapi/asm/poll.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/asm-generic/poll.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/eventpoll.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/indirect_call_wrapper.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/dst.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/rcuref.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/neighbour.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/tcp_states.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/net_tstamp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/l3mdev.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/fib_rules.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/fib_rules.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/fib_notifier.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/busy_poll.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ip.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ip.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ip.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/inet_sock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/request_sock.h \
    $(wildcard include/config/SYN_COOKIES) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/rstreason.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mptcp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mptcp_pm.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/hash.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/route.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/inetpeer.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ipv6.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ipv6.h \
    $(wildcard include/config/IPV6_ROUTER_PREF) \
    $(wildcard include/config/IPV6_ROUTE_INFO) \
    $(wildcard include/config/IPV6_OPTIMISTIC_DAD) \
    $(wildcard include/config/IPV6_SEG6_HMAC) \
    $(wildcard include/config/IPV6_MIP6) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ipv6.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/tcp.h \
    $(wildcard include/config/TCP_AO) \
    $(wildcard include/config/BPF) \
    $(wildcard include/config/TCP_MD5SIG) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/win_minmax.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/inet_connection_sock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/inet_timewait_sock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/timewait_sock.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/tcp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/udp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/udp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/jump_label_ratelimit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/if_inet6.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/inet_dscp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ip_fib.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/in_route.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/arp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/if_arp.h \
    $(wildcard include/config/FIREWIRE_NET) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_arp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ndisc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ipv6_stubs.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/icmpv6.h \
    $(wildcard include/config/NF_NAT) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/route.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/lwtunnel.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/lwtunnel.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/dsa.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/phy.h \
    $(wildcard include/config/LED_TRIGGER_PHY) \
    $(wildcard include/config/MDIO_DEVICE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/leds.h \
    $(wildcard include/config/LEDS_TRIGGERS) \
    $(wildcard include/config/LEDS_BRIGHTNESS_HW_CHANGED) \
    $(wildcard include/config/LEDS_TRIGGER_DISK) \
    $(wildcard include/config/LEDS_TRIGGER_MTD) \
    $(wildcard include/config/LEDS_TRIGGER_CAMERA) \
    $(wildcard include/config/LEDS_GPIO_REGISTER) \
    $(wildcard include/config/LEDS_TRIGGER_CPU) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/dt-bindings/leds/common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/linkmode.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mdio.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mdio.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mii.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mii.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mii_timestamper.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/iopoll.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/eee.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/platform_data/dsa.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/phylink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/devlink.h \
    $(wildcard include/config/NET_DEVLINK) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/devlink.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/firmware.h \
    $(wildcard include/config/FW_LOADER) \
    $(wildcard include/config/FW_UPLOAD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/switchdev.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/dst_metadata.h \
    $(wildcard include/config/DST_CACHE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ip_tunnels.h \
    $(wildcard include/config/IPV6_SIT_6RD) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/if_tunnel.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_tunnel.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/dsfield.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/gro_cells.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/inet_ecn.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netns/generic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/dst_cache.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ip6_fib.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ipv6_route.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ipv6_route.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ip6_route.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/addrconf.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/nexthop.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/macsec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/if_macsec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/gro.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/ip6_checksum.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/udp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/gso.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/hotdata.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/protocol.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/pkt_sched.h \
    $(wildcard include/config/NET_SCH_TAPRIO) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/pkt_cls.h \
    $(wildcard include/config/NET_CLS) \
    $(wildcard include/config/NET_EMATCH) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/act_api.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/xfrm.h \
    $(wildcard include/config/XFRM_SUB_POLICY) \
    $(wildcard include/config/NET_PKTGEN) \
    $(wildcard include/config/XFRM_MIGRATE) \
    $(wildcard include/config/XFRM_USER_COMPAT) \
    $(wildcard include/config/XFRM_INTERFACE) \
    $(wildcard include/config/DEBUG_INFO_BTF_MODULES) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/pfkeyv2.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/ipsec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/audit.h \
    $(wildcard include/config/AUDIT_COMPAT_GENERIC) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/audit_arch.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/audit.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/netfilter/nf_tables.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/fanotify.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/arch/arm/include/asm/syscall.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/tcx.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/bpf_mprog.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netpoll.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/iw_handler.h \
    $(wildcard include/config/WEXT_PRIV) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/wireless.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/wireless.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/dmaengine.h \
    $(wildcard include/config/DMA_ENGINE_RAID) \
    $(wildcard include/config/ASYNC_TX_ENABLE_CHANNEL_SWITCH) \
    $(wildcard include/config/DMA_ENGINE) \
    $(wildcard include/config/RAPIDIO_DMA_ENGINE) \
    $(wildcard include/config/ASYNC_TX_DMA) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/mpls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/mpls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/mpls.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/events/napi.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ftrace.h \
    $(wildcard include/config/HAVE_FUNCTION_GRAPH_FREGS) \
    $(wildcard include/config/FUNCTION_TRACER) \
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
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/events/net.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/events/skb.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/trace/events/qdisc.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/inetdevice.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/cpu_rmap.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/if_macvlan.h \
    $(wildcard include/config/MACVLAN) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/errqueue.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/errqueue.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter_netdev.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/netfilter/nf_conntrack_zones_common.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/crash_dump.h \
    $(wildcard include/config/CRASH_DUMP) \
    $(wildcard include/config/PROC_VMCORE_DEVICE_DUMP) \
    $(wildcard include/config/PROC_VMCORE) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/kexec.h \
    $(wildcard include/config/KEXEC_CORE) \
    $(wildcard include/config/KEXEC_FILE) \
    $(wildcard include/config/KEXEC_SIG) \
    $(wildcard include/config/SIGNED_PE_FILE_VERIFICATION) \
    $(wildcard include/config/KEXEC_ELF) \
    $(wildcard include/config/CRASH_HOTPLUG) \
    $(wildcard include/config/IMA_KEXEC) \
    $(wildcard include/config/KEXEC_JUMP) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/vmcore_info.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/elfcore.h \
    $(wildcard include/config/ARCH_BINFMT_ELF_EXTRA_PHDRS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/user.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sched/task_stack.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/magic.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/crash_reserve.h \
    $(wildcard include/config/ARCH_HAS_GENERIC_CRASHKERNEL_RESERVATION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/kexec.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/verification.h \
    $(wildcard include/config/SYSTEM_DATA_VERIFICATION) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/proc_fs.h \
    $(wildcard include/config/PROC_PID_ARCH_STATUS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/vmcore.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/sctp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/sctp.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/udp_tunnel.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/uapi/linux/net_namespace.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/pm_runtime.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/netdev_rx_queue.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/page_pool/types.h \
    $(wildcard include/config/PAGE_POOL_STATS) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/ptr_ring.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/page_pool/helpers.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/net/rps.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/include/linux/phy_link_topology.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/net/core/dev.h \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/net/core/devmem.h \
    $(wildcard include/config/NET_DEVMEM) \
  /home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/kernel-afdo-k1/kbase/source/net/core/net-sysfs.h \

net/core/dev.o: $(deps_net/core/dev.o)

$(deps_net/core/dev.o):
#SYMVER netdev_name_in_use 0x502a15b6
#SYMVER softnet_data 0x2045bc02
#SYMVER dev_add_pack 0x818d1025
#SYMVER __dev_remove_pack 0xa64482aa
#SYMVER dev_remove_pack 0xd4d15995
#SYMVER dev_get_iflink 0x7b258dd7
#SYMVER dev_fill_metadata_dst 0xd2886fb4
#SYMVER dev_fill_forward_path 0xce77c432
#SYMVER __dev_get_by_name 0xa0ad196e
#SYMVER dev_get_by_name_rcu 0x982604b4
#SYMVER dev_get_by_name 0xf89f9bbd
#SYMVER netdev_get_by_name 0x31410379
#SYMVER __dev_get_by_index 0x09118aa3
#SYMVER dev_get_by_index_rcu 0x8eb34aaf
#SYMVER dev_get_by_index 0xed613510
#SYMVER netdev_get_by_index 0x8a4c8ab6
#SYMVER dev_get_by_napi_id 0x5dfa9b40
#SYMVER dev_getbyhwaddr_rcu 0x962b96ad
#SYMVER dev_getbyhwaddr 0x05d7419b
#SYMVER dev_getfirstbyhwtype 0x82d9ef97
#SYMVER __dev_get_by_flags 0x6b243c01
#SYMVER dev_valid_name 0x62849ac7
#SYMVER dev_alloc_name 0x699e643a
#SYMVER dev_set_alias 0x1ef16341
#SYMVER netdev_features_change 0x9287ed80
#SYMVER netdev_state_change 0x959fe7c2
#SYMVER __netdev_notify_peers 0xb8f73893
#SYMVER netdev_notify_peers 0x3eba8091
#SYMVER dev_open 0x882eb20b
#SYMVER dev_close_many 0x58b4645c
#SYMVER dev_close 0x0d946a79
#SYMVER dev_disable_lro 0x3abb099a
#SYMVER netdev_cmd_to_name 0x3ae65f46
#SYMVER register_netdevice_notifier 0xd2da1048
#SYMVER unregister_netdevice_notifier 0x9d0d6206
#SYMVER register_netdevice_notifier_net 0x613d2510
#SYMVER unregister_netdevice_notifier_net 0x3d79569d
#SYMVER register_netdevice_notifier_dev_net 0xe8813e16
#SYMVER unregister_netdevice_notifier_dev_net 0x4c52b9f8
#SYMVER call_netdevice_notifiers 0xe1e7eb74
#SYMVER net_inc_ingress_queue 0x2c3054f9
#SYMVER net_dec_ingress_queue 0x46013233
#SYMVER net_inc_egress_queue 0x07be6905
#SYMVER net_dec_egress_queue 0x86f85114
#SYMVER tcf_sw_enabled_key 0x2018d9ea
#SYMVER netstamp_needed_key 0xf7f19d6d
#SYMVER net_enable_timestamp 0x54e6fcdd
#SYMVER net_disable_timestamp 0x199ed0cd
#SYMVER is_skb_forwardable 0x942e7f26
#SYMVER __dev_forward_skb 0x705ce9ba
#SYMVER dev_forward_skb 0xbe25322d
#SYMVER dev_nit_active 0x0bd253d8
#SYMVER dev_queue_xmit_nit 0xbbc12107
#SYMVER netdev_txq_to_tc 0x4a1ece82
#SYMVER __netif_set_xps_queue 0x7d7ef7ce
#SYMVER netif_set_xps_queue 0xc7e4c6c0
#SYMVER netdev_reset_tc 0x1689a7fb
#SYMVER netdev_set_tc_queue 0xa7313399
#SYMVER netdev_set_num_tc 0x66f0dbe9
#SYMVER netdev_unbind_sb_channel 0x813aa991
#SYMVER netdev_bind_sb_channel_queue 0x89392893
#SYMVER netdev_set_sb_channel 0xf62476cf
#SYMVER netif_set_real_num_tx_queues 0xb3ed86c7
#SYMVER netif_set_real_num_rx_queues 0xdf814651
#SYMVER netif_set_real_num_queues 0x61f1ceba
#SYMVER netif_set_tso_max_size 0x0f3f9896
#SYMVER netif_set_tso_max_segs 0x87cccf9d
#SYMVER netif_inherit_tso_max 0xa5f60c02
#SYMVER netif_get_num_default_rss_queues 0x0274dc2b
#SYMVER __netif_schedule 0xd390f141
#SYMVER netif_schedule_queue 0x17fe86c9
#SYMVER netif_tx_wake_queue 0x878fb5d6
#SYMVER dev_kfree_skb_irq_reason 0xc29a48a3
#SYMVER dev_kfree_skb_any_reason 0x6b93c335
#SYMVER netif_device_detach 0xc4f4e940
#SYMVER netif_device_attach 0x580c0e87
#SYMVER skb_checksum_help 0xfd5c597b
#SYMVER skb_crc32c_csum_help 0x6b526691
#SYMVER netdev_rx_csum_fault 0xe5d811c0
#SYMVER passthru_features_check 0xcd1cf7af
#SYMVER netif_skb_features 0xa9541d49
#SYMVER skb_csum_hwoffload_help 0x84398f80
#SYMVER validate_xmit_skb_list 0x648a471e
#SYMVER dev_loopback_xmit 0x8f7a9640
#SYMVER netdev_xmit_skip_txqueue 0xed8c384b
#SYMVER dev_pick_tx_zero 0xba325857
#SYMVER netdev_pick_tx 0x4dfb2a9b
#SYMVER __dev_queue_xmit 0xae93f377
#SYMVER __dev_direct_xmit 0x420c55dc
#SYMVER rps_needed 0x1b08a544
#SYMVER rfs_needed 0x31b854eb
#SYMVER rps_may_expire_flow 0xef0d5170
#SYMVER do_xdp_generic 0xb944ac93
#SYMVER __netif_rx 0x9d0e7f69
#SYMVER netif_rx 0xbba66cb4
#SYMVER netdev_is_rx_handler_busy 0x84be5c44
#SYMVER netdev_rx_handler_register 0x0ef1a3aa
#SYMVER netdev_rx_handler_unregister 0x5cb09b5b
#SYMVER netif_receive_skb_core 0x918b516d
#SYMVER netif_receive_skb 0x16335d47
#SYMVER netif_receive_skb_list 0x6b8bf149
#SYMVER __napi_schedule 0x669e788d
#SYMVER napi_schedule_prep 0x9c4d917b
#SYMVER __napi_schedule_irqoff 0x9c178483
#SYMVER napi_complete_done 0xd67806cc
#SYMVER napi_busy_loop 0x29604158
#SYMVER dev_set_threaded 0x920c6d53
#SYMVER netif_queue_set_napi 0x9626b018
#SYMVER netif_napi_add_weight 0xace6dc02
#SYMVER napi_disable 0x87df1252
#SYMVER napi_enable 0x650870d1
#SYMVER __netif_napi_del 0x4b3c85ce
#SYMVER netdev_has_upper_dev 0x9b1a560c
#SYMVER netdev_has_upper_dev_all_rcu 0x1d0ce913
#SYMVER netdev_has_any_upper_dev 0xf6b56ef3
#SYMVER netdev_master_upper_dev_get 0x716b47ea
#SYMVER netdev_adjacent_get_private 0xa0dad88e
#SYMVER netdev_upper_get_next_dev_rcu 0x2d47b0bc
#SYMVER netdev_walk_all_upper_dev_rcu 0xfb7350e5
#SYMVER netdev_lower_get_next_private 0x9af0872b
#SYMVER netdev_lower_get_next_private_rcu 0x9355017e
#SYMVER netdev_lower_get_next 0xc4f1020f
#SYMVER netdev_walk_all_lower_dev 0x637f1467
#SYMVER netdev_next_lower_dev_rcu 0xf7027765
#SYMVER netdev_walk_all_lower_dev_rcu 0x1a087240
#SYMVER netdev_lower_get_first_private_rcu 0xa229640f
#SYMVER netdev_master_upper_dev_get_rcu 0x1310a2d2
#SYMVER netdev_upper_dev_link 0x18064cf1
#SYMVER netdev_master_upper_dev_link 0xf3e7af5c
#SYMVER netdev_upper_dev_unlink 0xcb1afbca
#SYMVER netdev_adjacent_change_prepare 0x5bb5c8e2
#SYMVER netdev_adjacent_change_commit 0x9870666f
#SYMVER netdev_adjacent_change_abort 0x4762bb45
#SYMVER netdev_bonding_info_change 0x75462b61
#SYMVER netdev_offload_xstats_enable 0x629491b9
#SYMVER netdev_offload_xstats_disable 0x63587c7f
#SYMVER netdev_offload_xstats_enabled 0x9dd825a3
#SYMVER netdev_offload_xstats_get 0x5d028fb1
#SYMVER netdev_offload_xstats_report_delta 0x9fb41842
#SYMVER netdev_offload_xstats_report_used 0xd2d88506
#SYMVER netdev_offload_xstats_push_delta 0x3b3d8e76
#SYMVER netdev_get_xmit_slave 0x99830bd1
#SYMVER netdev_sk_get_lowest_dev 0x433c14ac
#SYMVER netdev_lower_dev_get_private 0x8316aa89
#SYMVER netdev_lower_state_changed 0x500fb6af
#SYMVER dev_set_promiscuity 0x78fb9f47
#SYMVER dev_set_allmulti 0xe99ddb82
#SYMVER dev_get_flags 0xf63a4371
#SYMVER dev_change_flags 0x4aec151f
#SYMVER __dev_set_mtu 0xd0f9baa1
#SYMVER dev_set_mtu 0x6e9a9d65
#SYMVER dev_pre_changeaddr_notify 0x7bf6626f
#SYMVER dev_set_mac_address 0x0f65eeb1
#SYMVER dev_set_mac_address_user 0xcf00e61b
#SYMVER dev_get_mac_address 0x4f988da4
#SYMVER dev_get_port_parent_id 0x81872f9a
#SYMVER netdev_port_same_parent_id 0x5a0d930a
#SYMVER dev_xdp_prog_count 0xe3e3a9df
#SYMVER dev_xdp_propagate 0xcdd5cbf5
#SYMVER netdev_update_features 0x7974d665
#SYMVER netdev_change_features 0xcae27b59
#SYMVER netif_stacked_transfer_operstate 0x2379eda5
#SYMVER netif_tx_stop_all_queues 0xad312047
#SYMVER register_netdevice 0xe058e970
#SYMVER init_dummy_netdev 0x6c8ecd27
#SYMVER register_netdev 0x90eea074
#SYMVER netdev_refcnt_read 0xa4330ee6
#SYMVER netdev_stats_to_stats64 0xb1b7d715
#SYMVER netdev_core_stats_inc 0x07a63ba3
#SYMVER dev_get_stats 0xf7742be6
#SYMVER dev_fetch_sw_netstats 0xd6c55c8f
#SYMVER dev_get_tstats64 0xd819e306
#SYMVER netdev_set_default_ethtool_ops 0xc8426a3a
#SYMVER netdev_sw_irq_coalesce_default_on 0x8be82e0f
#SYMVER alloc_netdev_mqs 0x958b6788
#SYMVER free_netdev 0xe7b6fbbb
#SYMVER alloc_netdev_dummy 0x1b7ea928
#SYMVER synchronize_net 0x609f1c7e
#SYMVER unregister_netdevice_queue 0xd40c1d98
#SYMVER unregister_netdevice_many 0x9fdecc31
#SYMVER unregister_netdev 0x3c4b2e27
#SYMVER __dev_change_net_namespace 0x516c638e
#SYMVER netdev_increment_features 0x69668826
#SYMVER netdev_compute_master_upper_features 0x9b1f2787
#SYMVER netdev_printk 0xa9a667d6
#SYMVER netdev_emerg 0xba8d22cb
#SYMVER netdev_alert 0x7257df18
#SYMVER netdev_crit 0x45e40c27
#SYMVER netdev_err 0x2b9dca47
#SYMVER netdev_warn 0x784bde7e
#SYMVER netdev_notice 0x03c5baeb
#SYMVER netdev_info 0x00d01aa1
