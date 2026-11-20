# AutoFDO for the Linux Kernel on 32-bit ARM: Research Results and Plan

Status as of 2026-11-20

## 1. Goal

Make the Linux kernel of our 32-bit ARM products **faster and smaller in memory** with sample-based profile-guided optimization (AutoFDO). The work covers the full chain:

1. collecting profiles on the device;
2. converting them with `llvm-profgen`;
3. building the kernel with the profile;
4. measuring the result with a statistically controlled method.

Upstream Linux added Clang AutoFDO in 6.13, but only for x86 with hardware branch sampling. The upstream ARM plan relies on SPE or ETM, which 32-bit ARM product kernels do not have. Our work targets this gap.

## 2. Platforms

| Platform | CPU / kernel | Role |
|---|---|---|
| Raspberry Pi 4 | Cortex-A72, 32-bit kernel (A32), linux-rpi 6.12, Clang 22.1.8 | Lab platform for the full end-to-end study |
| TV SoC (Novatek NT72671D) | 4 × Cortex-A53, 32-bit kernel 6.12.60, Tizen TV 10.0 | Product target; sampling and PMU studies done, kernel-level work waits for build inputs |
| Raspberry Pi 5 | Cortex-A76, 64-bit kernel | arm64 track only: the A76 supports AArch32 only at EL0, so it cannot run a 32-bit kernel |

## 3. Status Overview

| Item | Status | Basis |
|---|---|---|
| Kernel AutoFDO build support backported to 6.12 and enabled for 32-bit ARM | **Verified** | 5 upstream patches applied with no conflicts, plus 2 ARM32 patches; training kernel built, booted and validated on RPi4 |
| `llvm-profgen` kernel profile generation from IP samples | **Verified** | Works on live kernel samples: identity verified, 0 samples outside the kernel image, FS discriminators read correctly |
| Hot/cold function grouping without `-ffunction-sections` | **Verified (compiler level)** | Clang emits `.text.hot.` / `.text.unlikely.` sections on ARM32; effect in the profiled kernel is measured in the current step |
| Safe kernel switching on the board (firmware one-time boot) | **Verified** | Original boot chain untouched; a power cycle always returns to the original kernel |
| PMU cycle sampling on RPi4 and the TV SoC | **Verified** | TV SoC needs pinned events on a general counter (§4.5) |
| Taken-branch counting on the A53 (event 0x0C) | **Verified, as a metric only** | Counts taken branches exactly; not usable for sampling (§4.3) |
| End-to-end performance result of IP-based kernel AutoFDO on RPi4 | **In progress** | Training, profile, optimized kernel build, then paired measurement |
| Correction of the IRQ sampling shadow | **Planned (main research item)** | §4.2, §5 |
| Execution-count profile from kernel GCOV | **Planned (main route to branch information)** | §5 |
| Kernel size reduction (Thumb-2 baseline, cold-file `-Os`, hot-cold splitting) | **Planned** | Evaluated in 2 MiB steps (§4.6) |
| TV SoC kernel AutoFDO | **Waiting for inputs** | Needs the TV kernel's symbols (`vmlinux`/`System.map`) and build configuration |
| Taken-branch target sampling (branch information from PMU samples) | **Dropped** | Skid far longer than a basic block (§4.3) |
| Machine function splitting, basic-block sections, Propeller, ThinLTO on ARM32 | **Dropped** | Not supported by Clang or Kconfig for 32-bit ARM |
| Porting the kernel PGO instrumentation runtime | **Dropped** | Replaced by the mainline GCOV kernel support |
| BOLT for the kernel | **Dropped** | BOLT does not support 32-bit ARM |
| CoreSight ETM tracing | **On hold** | Not exposed on any of our boards; needs SoC information |
| Pseudo-probe profiles (CSSPGO) on ARM32 | **On hold** | Known Clang crash on ARMv7; low priority |

## 4. Research Results

### 4.1 Kernel AutoFDO is buildable and bootable on 32-bit ARM

- **Patches:** we backported the upstream build support (Kconfig, `Makefile.autofdo`, linker script markers for hot and unlikely text) to linux-rpi 6.12. Two local patches enable it for ARM:
  - one restricts function sections and machine function splitting to x86, where Clang supports them;
  - one enables the training configuration for the RPi4.
- **Validation:** the training kernel booted on RPi4 with all modules, display, logging and D-Bus working, and no new kernel warnings.
- **Training flags:** they are accepted on ARM32, but they grow kernel text by 178 KB (0.9%) compared with the same kernel without them.
- **Location:** the patches are on the Gerrit sandbox `sandbox/lhmax2025/afdo_kernel_arm32`.

### 4.2 IRQ shadow: the main accuracy problem of ARM32 kernel sampling

On 32-bit ARM the PMU overflow interrupt is an ordinary IRQ; there is no NMI. While interrupts are disabled, the sample is delayed until they are re-enabled. Code that runs with interrupts disabled (the scheduler, spinlock-protected sections) then appears as time spent at the re-enable point.

Share of kernel samples on an IRQ re-enable instruction or the instruction right after it:

| Workload (RPi4) | Share |
|---|---:|
| pipe (scheduler/IPC) | 56% (60.6% on our own training kernel) |
| system call loop | 60% |
| anonymous memory faults | 47% |
| video decode | 40% |
| tmpfs I/O | 35% |

The TV SoC uses the same ordinary-interrupt PMU, so the problem applies to the product. Upstream x86 and arm64 use NMI-based or hardware-recorded samples and do not face it. Correcting it is our main research item (§5).

### 4.3 Sampling skid on the TV SoC, and why branch-target sampling is dropped

- **Skid:** measured with a single-branch test program on the A53, the sample lands about **106 cycles** after the triggering event, with very little spread (p99 113 cycles). That is 107–212 instructions, depending on how fast the code runs.
- **Taken-branch counting works:** event 0x0C counts exactly the taken branches. Adding 67 million not-taken branches changed the count by 53.
- **Taken-branch sampling fails:** because the skid spans many basic blocks, samples cannot identify the branch that triggered them. Only 1.3% of samples landed at a block entry. Branch information therefore cannot be recovered from PMU samples on these cores. The Cortex-A72 does not implement the needed events at all.
- **Effect on plain IP profiles:** the same skid smears them at block level. Function-level hotness stays usable.

### 4.4 Most CPU time on the TV is in the kernel

| TV SoC workload | Kernel share of cycle samples |
|---|---:|
| Idle UI (panel on, no input) | 86.5% |
| Scheduler/IPC benchmark | 91.1% |

This confirms that the kernel is the right optimization target for the product.

### 4.5 TV SoC constraints

- **No `/proc/kallsyms`:** kernel symbols must come from the kernel build (`System.map` and `vmlinux`).
- **A built-in PMU monitor (PMUMON) holds PMU counters:**
  - ordinary per-process counting gets no time;
  - pinned events run 100% of the time;
  - sampling on the dedicated cycle counter corrupts PMUMON's statistics, while sampling on event 0x11 (cycles on a general counter) does not and gives the same distribution (within 1.5%).

  Our standard on the TV is therefore pinned `r11` sampling.
- **No CoreSight devices are exposed.**
- **Programs run only as root, from `/root`.**

### 4.6 Memory is quantized in 2 MiB steps

- **Why:** with LPAE and strict kernel memory protection, kernel text is aligned to 2 MiB sections. A text reduction only frees memory once it crosses a 2 MiB boundary.
- **The reverse risk:** text growth past the boundary costs a full 2 MiB more.
- **Current headroom:** the RPi4 training kernel has 922 KB left before the next boundary.
- **Consequence:** size work targets savings that cross a boundary, and every optimized kernel reports which 2 MiB step it falls in.
- **TV kernel:** its configuration is needed to confirm the same rule; its kernel code is 8.2 MiB.

### 4.7 Observation outside AutoFDO

On the RPi4 pipe workload, mapping high-memory pages in and out (`__kmap_local_pfn_prot`, `kunmap_local_indexed`) takes about 7.5% of kernel samples. That is the cost of a 32-bit kernel on a 4 GB board. A kernel configuration choice may matter here as much as compiler work; it will be evaluated separately.

### 4.8 Measurement method

Results will be reported with confidence intervals. The method:
- **Paired comparisons:** kernels are compared in paired AB/BA blocks across reboots.
- **Run count:** the number of blocks is set from a cross-reboot A/A pilot.
- **Layout control:** a kernel with randomly shuffled sections measures how much layout alone changes performance. 32-bit ARM has no KASLR, so a fixed layout could otherwise be mistaken for a profile effect.
- **Boot gates:** each boot must pass identity checks (build-id, command line, normalized device tree, modules) and a quiet-system gate before timing starts.

The primary benchmark is the scheduler/IPC pipe test. The others are a page-fault test, tmpfs, a system call loop, a held-out fork/exec test that is not used for training, and a video decode control.

## 5. Plan

| Phase | Content | Exit criterion |
|---|---|---|
| **P1 (current)** | RPi4 end-to-end: sampling on the training kernel (AutoFDO build support, no profile), profile generation, optimized kernel, layout control, paired measurement; reporting of the IRQ shadow share and the share of samples AutoFDO can act on | Verdict with confidence interval on the primary benchmark |
| **P2** | **IRQ shadow correction:** move delayed samples back to the calling code using kernel call stacks. **GCOV count profile:** a lab build with mainline kernel GCOV gives real execution counts, converted to a sample profile; it is free of the shadow and the skid, and also serves as ground truth. Plus ftrace function counts for calibration, and a Thumb-2 kernel size baseline | Corrected or count-based profile measurably better than the plain IP profile |
| **P3** | TV SoC: build the TV kernel with AutoFDO support and apply the P1/P2 chain with the TV sampling rules | TV kernel builds and can be deployed in the lab |
| **P4** | **Hybrid profile:** device samples give function hotness, lab counts give branch ratios inside functions. **Coverage-based size reduction** report. Hardware sampling through the external debug PC register if the SoC allows it | Hybrid profile not worse than either single source |

## 6. Expected Innovation

1. **Correction of interrupt-delayed sampling for 32-bit ARM kernels**, evaluated against execution-count ground truth. No upstream solution exists.
2. **Count-based kernel profiles from mainline GCOV.** They need no hardware branch recording and use no product runtime changes.
3. **Hybrid profiles** that combine device sampling with lab execution counts.
4. **Size optimization measured in the real 2 MiB memory steps** of the product kernel.
