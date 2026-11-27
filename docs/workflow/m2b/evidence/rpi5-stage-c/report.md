# Experiment m2b-ffmpeg-rpi5-aarch64-01

profgen explicit conservative strategy; defaults not statistically validated

Verdict: **inconclusive**

| Section | Recorded value |
|---|---|
| artifacts | {"libavcodec": {"build_id": "5b6a19d0f3a75ec297d863e883bd361c4aab3245", "debug_path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-s5-board-20261126/verified-builds/PGO/extracted/usr/lib/debug/usr/lib64/libavcodec.so.62.11.100.debug", "debug_sha256": "c2352b6ae3f0a3d316b2c6f2a4061de1f521324d38a5860899ab2322f3815eaa", "isa": "a64", "path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-s5-board-20261126/verified-builds/PGO/extracted/usr/lib64/libavcodec.so.62.11.100", "real_name": "libavcodec.so.62.11.100", "sha256": "3cd6f5a81f52e1f79e044df6018a158d6a9c92384d19eec1db819de8c2f4fadc", "soname": "libavcodec.so.62"}, "libavutil": {"build_id": "1d4bde182c0ecaf03b0241c8ca6462655de26327", "debug_path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-s5-board-20261126/verified-builds/PGO/extracted/usr/lib/debug/usr/lib64/libavutil.so.60.8.100.debug", "debug_sha256": "14b2516b0fa15071f86b6da279f3f36773f193787cb9a4f6c2c945d5a1c52a6c", "isa": "a64", "path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-s5-board-20261126/verified-builds/PGO/extracted/usr/lib64/libavutil.so.60.8.100", "real_name": "libavutil.so.60.8.100", "sha256": "322981e41aaf5127e78e0b95b7daf00d011cfdcccc5953f85fe33d1d8fe7d430", "soname": "libavutil.so.60"}} |
| board_identity | {"arch": "aarch64", "build_id": "tizen-unified-toolchain_20261118.083201", "kernel": "6.12.80-arm64-rpi4-v8", "model": "Raspberry Pi 5 Model B Rev 1.1"} |
| build_lock | {"passed": true, "checks": {"AFDO": {"differences": [], "passed": true}, "BASE-r": {"differences": [], "passed": true}, "PGO": {"differences": [], "passed": true}, "PGOGEN": {"differences": [], "passed": true}}} |
| cleanup_pending | [] |
| code_shares | {"status": "diagnostic only"} |
| consumption | {"afdo": {"passed": true, "staged_sha256": "db4d4c196cde3afb20803580ed5317d83a7d4a95f0d8f830c5394f1536b99d5a", "targets": {"libavcodec": {"examples": [{"DebugLoc": {"Column": 14, "File": "libavcodec/h2645_sei.c", "Line": 761}, "Function": "ff_h2645_sei_to_frame", "Name": "AppliedSamples", "NumSamples": 2, "Pass": "sample-profile-impl", "document": 1, "object": "libavcodec/h2645_sei.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h2645_sei.opt.yaml"}, {"DebugLoc": {"Column": 26, "File": "libavcodec/h2645_sei.c", "Line": 787}, "Function": "ff_h2645_sei_to_frame", "Name": "AppliedSamples", "NumSamples": 2, "Pass": "sample-profile-impl", "document": 2, "object": "libavcodec/h2645_sei.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h2645_sei.opt.yaml"}, {"DebugLoc": {"Column": 47, "File": "libavcodec/h2645_sei.c", "Line": 887}, "Function": "ff_h2645_sei_to_frame", "Name": "AppliedSamples", "NumSamples": 2, "Pass": "sample-profile-impl", "document": 3, "object": "libavcodec/h2645_sei.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h2645_sei.opt.yaml"}, {"DebugLoc": {"Column": 14, "File": "libavcodec/h2645_sei.c", "Line": 681}, "Function": "_ZL22h2645_sei_to_side_dataP14AVCodecContextP8H2645SEIPPP15AVFrameSideDataPi.__uniq.175561029008273135802141817102909425490", "Name": "AppliedSamples", "NumSamples": 3, "Pass": "sample-profile-impl", "document": 33, "object": "libavcodec/h2645_sei.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h2645_sei.opt.yaml"}, {"DebugLoc": {"Column": 32, "File": "libavcodec/mpegutils.c", "Line": 160}, "Function": "ff_print_debug_info2", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 1, "object": "libavcodec/mpegutils.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/mpegutils.opt.yaml"}, {"DebugLoc": {"Column": 16, "File": "libavcodec/mpegutils.c", "Line": 247}, "Function": "ff_print_debug_info2", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 2, "object": "libavcodec/mpegutils.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/mpegutils.opt.yaml"}, {"DebugLoc": {"Column": 12, "File": "libavcodec/h264_sei.c", "Line": 307}, "Function": "ff_h264_sei_stereo_mode", "Name": "AppliedSamples", "NumSamples": 2, "Pass": "sample-profile-impl", "document": 1, "object": "libavcodec/h264_sei.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h264_sei.opt.yaml"}, {"DebugLoc": {"Column": 29, "File": "libavcodec/h2645_parse.c", "Line": 476}, "Function": "ff_h2645_packet_split", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 13, "object": "libavcodec/h2645_parse.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h2645_parse.opt.yaml"}, {"DebugLoc": {"Column": 17, "File": "libavcodec/h2645_parse.c", "Line": 428}, "Function": "ff_h2645_packet_split", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 14, "object": "libavcodec/h2645_parse.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h2645_parse.opt.yaml"}, {"DebugLoc": {"Column": 17, "File": "libavcodec/h2645_parse.h", "Line": 138}, "Function": "ff_h2645_packet_split", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 15, "object": "libavcodec/h2645_parse.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavcodec/h2645_parse.opt.yaml"}], "positive_records": 1804, "reasons": [], "status": "verified"}, "libavutil": {"examples": [{"DebugLoc": {"Column": 10, "File": "libavutil/buffer.c", "Line": 141}, "Function": "av_buffer_unref", "Name": "AppliedSamples", "NumSamples": 3, "Pass": "sample-profile-impl", "document": 3, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 18, "File": "libavutil/buffer.c", "Line": 141}, "Function": "av_buffer_unref", "Name": "AppliedSamples", "NumSamples": 18, "Pass": "sample-profile-impl", "document": 4, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 34, "File": "libavutil/buffer.c", "Line": 132}, "Function": "av_buffer_unref", "Name": "AppliedSamples", "NumSamples": 2, "Pass": "sample-profile-impl", "document": 5, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 12, "File": "libavutil/buffer.c", "Line": 133}, "Function": "av_buffer_unref", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 6, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 24, "File": "libavutil/buffer.c", "Line": 105}, "Function": "av_buffer_replace", "Name": "AppliedSamples", "NumSamples": 2, "Pass": "sample-profile-impl", "document": 13, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 10, "File": "libavutil/buffer.c", "Line": 37}, "Function": "av_buffer_realloc", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 23, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 1, "File": "libavutil/buffer.c", "Line": 231}, "Function": "av_buffer_realloc", "Name": "AppliedSamples", "NumSamples": 1, "Pass": "sample-profile-impl", "document": 24, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 30, "File": "libavutil/buffer.c", "Line": 162}, "Function": "av_buffer_get_ref_count", "Name": "AppliedSamples", "NumSamples": 7, "Pass": "sample-profile-impl", "document": 31, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 19, "File": "libavutil/buffer.c", "Line": 35}, "Function": "av_buffer_create", "Name": "AppliedSamples", "NumSamples": 2, "Pass": "sample-profile-impl", "document": 34, "object": "libavutil/buffer.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/buffer.opt.yaml"}, {"DebugLoc": {"Column": 19, "File": "libavutil/imgutils.c", "Line": 45}, "Function": "av_image_get_linesize", "Name": "AppliedSamples", "NumSamples": 20, "Pass": "sample-profile-impl", "document": 3, "object": "libavutil/imgutils.opt.yaml", "remark_file": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/run-3/roots/AFDO-1795694894406273603/local/BUILD-ROOTS/scratch.aarch64.0/home/abuild/rpmbuild/BUILD/ffmpeg-8.0.1/libavutil/imgutils.opt.yaml"}], "positive_records": 63, "reasons": [], "status": "verified"}}}, "passed": true, "pgo": {"changed_text": {"libavcodec": true, "libavutil": true}, "coverage": {"libavcodec": {"covered_functions": 211, "instrumented_functions": 4530, "ratio": 0.04657836644591611}, "libavutil": {"covered_functions": 83, "instrumented_functions": 1127, "ratio": 0.07364685004436557}}, "passed": true, "staged_sha256": "0da9065bb8cb664711f157a68250c51f2eee2ed609d61e8dfa72dd4c64f9603e", "warning_audit": {"counts": {}, "missing_hot_compile_objects": [], "outdated_gate": [], "passed": true, "records": [], "top20": [{"function": "libavcodec/h264_cabac.c;_ZL36decode_cabac_residual_nondc_internalPK11H264ContextP16H264SliceContextPsiiPKhPKji.__uniq.27894887720519182085624620829320312160", "max_count": 144160437, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "libavcodec/h264_cabac.c;_ZL18get_cabac_noinlineP12CABACContextPh.__uniq.27894887720519182085624620829320312160", "max_count": 119485803, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "ff_h264_filter_mb", "max_count": 49952877, "object": "libavcodec/h264_loopfilter.o", "pgogen_object_sha256": "7fd44362e19a4ef11c451f644314260638c2311e00d5ff0e296dacab83a898f9"}, {"function": "libavcodec/h264_loopfilter.c;_ZL8check_mvP16H264SliceContextlli.__uniq.275345673349404074195048302594725744325", "max_count": 41851545, "object": "libavcodec/h264_loopfilter.o", "pgogen_object_sha256": "7fd44362e19a4ef11c451f644314260638c2311e00d5ff0e296dacab83a898f9"}, {"function": "libavcodec/h264_cabac.c;_ZL19decode_cabac_mb_mvdP16H264SliceContextiiPi.__uniq.27894887720519182085624620829320312160", "max_count": 38296167, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "libavcodec/h264_cabac.c;_ZL18fill_decode_cachesPK11H264ContextP16H264SliceContexti.__uniq.27894887720519182085624620829320312160", "max_count": 29404542, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "ff_h264_decode_mb_cabac", "max_count": 23570835, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "libavcodec/h264_mb.c;_ZL20mc_part_420_simple_8PK11H264ContextP16H264SliceContextiiiiPhS4_S4_iiPKPFvS4_PKhlEPFvS4_S6_liiiESA_SC_PKPFvS4_liiiiEPKPFvS4_S4_liiiiiEii.__uniq.237198308776883668208751996125870213978", "max_count": 21263538, "object": "libavcodec/h264_mb.o", "pgogen_object_sha256": "176e77b256c76fd66c78a3ebc1af249e8eb949121734866e5326cf85d01ebaaa"}, {"function": "ff_h264_hl_decode_mb", "max_count": 19440000, "object": "libavcodec/h264_mb.o", "pgogen_object_sha256": "176e77b256c76fd66c78a3ebc1af249e8eb949121734866e5326cf85d01ebaaa"}, {"function": "libavcodec/h264_slice.c;_ZL12decode_sliceP14AVCodecContextPv.__uniq.248544299231367077551893488431358088102", "max_count": 19440000, "object": "libavcodec/h264_slice.o", "pgogen_object_sha256": "1a248e8759fa4bd0c88253ec394c3fd4f7fd5970ad8fbf3667ca7e810b0af684"}, {"function": "libavcodec/h264_cabac.c;_ZL21fill_decode_neighborsPK11H264ContextP16H264SliceContexti.__uniq.27894887720519182085624620829320312160", "max_count": 19440000, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "libavcodec/h264_slice.c;_ZL11loop_filterPK11H264ContextP16H264SliceContextii.__uniq.248544299231367077551893488431358088102", "max_count": 19440000, "object": "libavcodec/h264_slice.o", "pgogen_object_sha256": "1a248e8759fa4bd0c88253ec394c3fd4f7fd5970ad8fbf3667ca7e810b0af684"}, {"function": "libavcodec/h264_cabac.c;_ZL20decode_cabac_mb_skipPK11H264ContextP16H264SliceContextii.__uniq.27894887720519182085624620829320312160", "max_count": 19256400, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "ff_h264_pred_direct_motion", "max_count": 18966162, "object": "libavcodec/h264_direct.o", "pgogen_object_sha256": "ed4a67ad300018fd6863c21e50eb4eddedf991b383b52894c4201357372e4546"}, {"function": "libavcodec/h264_mb.c;_ZL21hl_decode_mb_simple_8PK11H264ContextP16H264SliceContext.__uniq.237198308776883668208751996125870213978", "max_count": 17729082, "object": "libavcodec/h264_mb.o", "pgogen_object_sha256": "176e77b256c76fd66c78a3ebc1af249e8eb949121734866e5326cf85d01ebaaa"}, {"function": "ff_h264_filter_mb_fast", "max_count": 16064076, "object": "libavcodec/h264_loopfilter.o", "pgogen_object_sha256": "7fd44362e19a4ef11c451f644314260638c2311e00d5ff0e296dacab83a898f9"}, {"function": "ff_emulated_edge_mc_8", "max_count": 16006068, "object": "libavcodec/videodsp.o", "pgogen_object_sha256": "14871af22d6117748cf78585966d3d922522205e9903f2a6ac29eb6ac03fa31b"}, {"function": "libavcodec/h264_cabac.c;_ZL16get_cabac_bypassP12CABACContext.__uniq.27894887720519182085624620829320312160", "max_count": 13655784, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}, {"function": "libavcodec/h264_direct.c;_ZL22await_reference_mb_rowPK11H264ContextP7H264Refi.__uniq.296751724182731167774237165245098469956", "max_count": 13564773, "object": "libavcodec/h264_direct.o", "pgogen_object_sha256": "ed4a67ad300018fd6863c21e50eb4eddedf991b383b52894c4201357372e4546"}, {"function": "libavcodec/h264_cabac.c;_ZL34decode_cabac_mb_intra4x4_pred_modeP16H264SliceContexti.__uniq.27894887720519182085624620829320312160", "max_count": 10715148, "object": "libavcodec/h264_cabac.o", "pgogen_object_sha256": "50f78042d48369a5014b081535b754c4227b3e1be17bd526ca044d417ac70d92"}], "unprofiled_gate": []}, "warning_counts": {}}} |
| experiment_id | "m2b-ffmpeg-rpi5-aarch64-01" |
| limitations | ["One RPi5; single-threaded decode; ToS primary; Sintel supplementary; no multiple-comparison correction", "Firmware throttle history and voltage status unknown on this board", "profgen explicit conservative strategy; defaults not statistically validated"] |
| measurement_plan | {"pgo-vs-afdo": {"sintel-1080p-60": {"N": 40, "analysis_sha256": "66318a939e9eb8bca7b15ae6076133431290226d27a3f0682fe8b18ef3312887", "bootstrap_seed": 2026112753, "candidate": "PGO", "control": "AFDO", "epsilon": 0.01, "input": {"duration": 60, "id": "sintel-1080p-60", "oracle": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "frames": 1440, "threads": 1}, "path": "/opt/afdo_agent/inputs/sintel_1080p_h264_60s.mp4", "role": "test-secondary", "sha256": "b1c762e322350cecb04a38509050d320892ff8cbc8b2a7113418d5ecba4ad843", "start": 0}, "multiple_comparison_correction": false, "order": [["AFDO", "PGO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"]], "order_seed": 2026112743, "pilot_cv": 0.02190599022870312, "primary": false, "registered_time": 1795773743.2433338, "warmup": 2}, "tos-720p-60": {"N": 24, "analysis_sha256": "66318a939e9eb8bca7b15ae6076133431290226d27a3f0682fe8b18ef3312887", "bootstrap_seed": 2026112752, "candidate": "PGO", "control": "AFDO", "epsilon": 0.01, "input": {"duration": 60, "id": "tos-720p-60", "oracle": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "frames": 1800, "threads": 1}, "path": "/opt/afdo_agent/inputs/tos_720p_h264_60s.mp4", "role": "test", "sha256": "280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1", "start": 0}, "multiple_comparison_correction": false, "order": [["PGO", "AFDO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["PGO", "AFDO"], ["AFDO", "PGO"], ["AFDO", "PGO"], ["AFDO", "PGO"]], "order_seed": 2026112742, "pilot_cv": 0.006905655829379111, "primary": false, "registered_time": 1795773226.8855157, "warmup": 2}}, "pgo-vs-base": {"sintel-1080p-60": {"N": 17, "analysis_sha256": "66318a939e9eb8bca7b15ae6076133431290226d27a3f0682fe8b18ef3312887", "bootstrap_seed": 2026112751, "candidate": "PGO", "control": "BASE", "epsilon": 0.01, "input": {"duration": 60, "id": "sintel-1080p-60", "oracle": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "frames": 1440, "threads": 1}, "path": "/opt/afdo_agent/inputs/sintel_1080p_h264_60s.mp4", "role": "test-secondary", "sha256": "b1c762e322350cecb04a38509050d320892ff8cbc8b2a7113418d5ecba4ad843", "start": 0}, "multiple_comparison_correction": false, "order": [["PGO", "BASE"], ["PGO", "BASE"], ["PGO", "BASE"], ["PGO", "BASE"], ["PGO", "BASE"], ["BASE", "PGO"], ["PGO", "BASE"], ["BASE", "PGO"], ["BASE", "PGO"], ["PGO", "BASE"], ["BASE", "PGO"], ["BASE", "PGO"], ["PGO", "BASE"], ["BASE", "PGO"], ["BASE", "PGO"], ["BASE", "PGO"], ["BASE", "PGO"]], "order_seed": 2026112741, "pilot_cv": 0.005856864871888289, "primary": false, "registered_time": 1795772856.9371288, "warmup": 2}, "tos-720p-60": {"N": 30, "analysis_sha256": "66318a939e9eb8bca7b15ae6076133431290226d27a3f0682fe8b18ef3312887", "bootstrap_seed": 2026112750, "candidate": "PGO", "control": "BASE", "epsilon": 0.01, "input": {"duration": 60, "id": "tos-720p-60", "oracle": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "frames": 1800, "threads": 1}, "path": "/opt/afdo_agent/inputs/tos_720p_h264_60s.mp4", "role": "test", "sha256": "280fbd41f8772491ebe784aa19a3caed3bb1e8b2e64daef1d2a5a284d1f38ad1", "start": 0}, "multiple_comparison_correction": false, "order": [["PGO", "BASE"], ["BASE", "PGO"], ["PGO", "BASE"], ["PGO", "BASE"], ["BASE", "PGO"], ["PGO", "BASE"], ["PGO", "BASE"], ["BASE", "PGO"], ["BASE", "PGO"], ["PGO", "BASE"], ["PGO", "BASE"], ["BASE", "PGO"], ["PGO", "BASE"], ["BASE", "PGO"], ["BASE", "PGO"], ["PGO", "BASE"], ["BASE", "PGO"], ["BASE", "PGO"], ["BASE", "PGO"], ["BASE", "PGO"], ["PGO", "BASE"], ["PGO", "BASE"], ["BASE", "PGO"], ["PGO", "BASE"], ["PGO", "BASE"], ["BASE", "PGO"], ["PGO", "BASE"], ["PGO", "BASE"], ["BASE", "PGO"], ["BASE", "PGO"]], "order_seed": 2026112740, "pilot_cv": 0.007800545341936291, "primary": true, "registered_time": 1795772307.9420567, "warmup": 2}}} |
| oracle | {"passed": true, "records": {"pgo-post-AFDO-bbb-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-post-AFDO-sintel-1080p-60": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "eos": true, "frames": 1440, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)540/409, chroma-site=(string)mpeg2, colorimetry=(string)2:3:0:0, framerate=(fraction)24/1", "status": "ok", "threads": 1}, "pgo-post-AFDO-tos-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-post-BASE-bbb-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-post-BASE-sintel-1080p-60": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "eos": true, "frames": 1440, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)540/409, chroma-site=(string)mpeg2, colorimetry=(string)2:3:0:0, framerate=(fraction)24/1", "status": "ok", "threads": 1}, "pgo-post-BASE-tos-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-post-PGO-bbb-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-post-PGO-sintel-1080p-60": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "eos": true, "frames": 1440, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)540/409, chroma-site=(string)mpeg2, colorimetry=(string)2:3:0:0, framerate=(fraction)24/1", "status": "ok", "threads": 1}, "pgo-post-PGO-tos-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-pre-AFDO-bbb-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-pre-AFDO-sintel-1080p-60": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "eos": true, "frames": 1440, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)540/409, chroma-site=(string)mpeg2, colorimetry=(string)2:3:0:0, framerate=(fraction)24/1", "status": "ok", "threads": 1}, "pgo-pre-AFDO-tos-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-pre-BASE-bbb-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-pre-BASE-sintel-1080p-60": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "eos": true, "frames": 1440, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)540/409, chroma-site=(string)mpeg2, colorimetry=(string)2:3:0:0, framerate=(fraction)24/1", "status": "ok", "threads": 1}, "pgo-pre-BASE-tos-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-pre-PGO-bbb-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "3a4c3820c576697edd4ca34f3532c8af8ffaf04687955c5d6b35215b9b06c814", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}, "pgo-pre-PGO-sintel-1080p-60": {"bytes": 4478976000, "caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080", "digest": "91d171c0cd99266d0efeee7b9023a77bf39c925ec372bcd1d1e7efaf08ecd193", "eos": true, "frames": 1440, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1920, height=(int)1080, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)540/409, chroma-site=(string)mpeg2, colorimetry=(string)2:3:0:0, framerate=(fraction)24/1", "status": "ok", "threads": 1}, "pgo-pre-PGO-tos-720p-60": {"bytes": 2488320000, "caps": "I420,1280x720,30/1,progressive,1/1", "digest": "4c2610c37b7790240c9158277981ed9c3ac81399e3e9df554ffebb2d2ff80c4e", "eos": true, "frames": 1800, "maps_checked": 1, "raw_caps": "video/x-raw, format=(string)I420, width=(int)1280, height=(int)720, interlace-mode=(string)progressive, pixel-aspect-ratio=(fraction)1/1, chroma-site=(string)mpeg2, framerate=(fraction)30/1", "status": "ok", "threads": 1}}} |
| quality | {"instrumentation": {"compatible": true, "identity": "verified", "publishable": true, "target_coverage": {"libavcodec": {"covered_functions": 211, "instrumented_functions": 4530, "ratio": 0.04657836644591611}, "libavutil": {"covered_functions": 83, "instrumented_functions": 1127, "ratio": 0.07364685004436557}}}} |
| rounds | 222 |
| statistics | {"clean_sensitivity": {"baseline_CV": 0.017008971202835246, "bootstrap_CI95": [-0.0197576881948349, -0.005005162305147587], "estimate": -0.012405441553449198, "median_ratio_minus_one": -0.013754110193279434, "n": 30, "t_CI95": [-0.020233050735285227, -0.004515295596363152], "verdict": "inconclusive"}, "flag_imbalance": {"counts": {"candidate": 0, "control": 0}, "decision": "PM decision 2026-11-17", "difference": 0, "threshold": 3}, "flagged": 0, "missing": 0, "primary": {"baseline_CV": 0.017008971202835246, "bootstrap_CI95": [-0.0197576881948349, -0.005005162305147587], "estimate": -0.012405441553449198, "median_ratio_minus_one": -0.013754110193279434, "n": 30, "t_CI95": [-0.020233050735285227, -0.004515295596363152], "verdict": "inconclusive"}, "repetitions": 20000, "sampling": "random.Random.choices; linear percentiles", "seed": 2026112750} |
| telemetry_manifest | {"frequency": ["/sys/devices/system/cpu/cpufreq/policy0/scaling_cur_freq", "/sys/devices/system/cpu/cpufreq/policy0/cpuinfo_cur_freq"], "temperature": ["/sys/class/thermal/thermal_zone0/temp"], "voltage": []} |
| tools | {"libLLVM": {"path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/profgen-release-20261114c/extracted/usr/lib64/libLLVM.so.22.1", "sha256": "bc67bdd5b798822ae06b8605b00d4ed506a30d444ee10a511999fd27eb05ef6e"}, "loader": {"path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/GBS-ROOT-LLVM-RELEASE-20261114c/local/BUILD-ROOTS/scratch.x86_64.0/lib64/ld-linux-x86-64.so.2", "sha256": "bc27f3613fc50e29c9fba03290be3f5f6e4235fcc584cf9d7b20ed97a4852a85"}, "profdata": {"path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/profgen-release-20261114c/extracted/usr/bin/llvm-profdata", "sha256": "1700cc8924ba608c773a73b7550025189e5e2af3a994ef58ddc6009933d0977e"}, "profgen": {"path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/profgen-release-20261114c/extracted/usr/bin/llvm-profgen", "sha256": "67ad21faba787d276a80673c1f324f7c0591d28d76bd37a8bd57de0d86426be6"}} |

## Paired comparisons

| Comparison | Input | N | Pilot CV | Relative time | Bootstrap 95% CI | t 95% CI | Verdict |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| pgo-vs-afdo | sintel-1080p-60 | 40 | 2.191% | -1.380% | [-1.870%, -0.879%] | [-1.894%, -0.863%] | inconclusive |
| pgo-vs-afdo | tos-720p-60 | 24 | 0.691% | -1.334% | [-2.030%, -0.606%] | [-2.096%, -0.565%] | inconclusive |
| pgo-vs-base | sintel-1080p-60 | 17 | 0.586% | -1.187% | [-1.872%, -0.429%] | [-1.985%, -0.383%] | inconclusive |
| pgo-vs-base | tos-720p-60 | 30 | 0.780% | -1.241% | [-1.976%, -0.501%] | [-2.023%, -0.452%] | inconclusive |

## Measurement diagnostics

| Comparison | Input | Flagged blocks | Flag imbalance (difference / threshold) | Retries | Effective MHz (control / PGO) | Frequency confounding | Temperature °C (control / PGO range) |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| pgo-vs-afdo | sintel-1080p-60 | 0 | 0 / 4 | 0 | 2399.80 / 2399.79 | False | 38.6–45.8 / 39.7–45.8 |
| pgo-vs-afdo | tos-720p-60 | 0 | 0 / 3 | 0 | 2399.79 / 2399.82 | False | 39.1–45.2 / 39.1–45.2 |
| pgo-vs-base | sintel-1080p-60 | 0 | 0 / 2 | 0 | 2399.86 / 2399.84 | False | 39.7–45.2 / 39.7–45.2 |
| pgo-vs-base | tos-720p-60 | 0 | 0 / 3 | 0 | 2399.80 / 2399.76 | False | 39.1–45.8 / 38.6–45.2 |

## Mechanism counts

Diagnostic counts are collected separately from paired timing.

| Comparison | Event | Pairs | Control median | PGO median | Median paired relative difference |
| --- | --- | ---: | ---: | ---: | ---: |
| pgo-vs-afdo | branch-misprediction | 5 | 223905140 | 222672205 | -0.564% |
| pgo-vs-afdo | cycles | 5 | 29783728208 | 29335161024 | -1.094% |
| pgo-vs-afdo | frontend-stall | 5 | 1952351157 | 1755254380 | -10.335% |
| pgo-vs-afdo | frontend-stall-slots | 0 | None | None | — |
| pgo-vs-afdo | instructions | 5 | 38469569190 | 37405531764 | -2.766% |
| pgo-vs-afdo | l1i-refill | 5 | 80278688 | 72474632 | -9.772% |
| pgo-vs-afdo | l1i-tlb-refill | 5 | 2903382 | 2413274 | -16.571% |
| pgo-vs-base | branch-misprediction | 5 | 221673972 | 222672205 | +0.463% |
| pgo-vs-base | cycles | 5 | 29853666939 | 29335161024 | -1.684% |
| pgo-vs-base | frontend-stall | 5 | 1854187109 | 1755254380 | -4.557% |
| pgo-vs-base | frontend-stall-slots | 0 | None | None | — |
| pgo-vs-base | instructions | 5 | 39619717152 | 37405531764 | -5.589% |
| pgo-vs-base | l1i-refill | 5 | 51642098 | 72474632 | +41.285% |
| pgo-vs-base | l1i-tlb-refill | 5 | 3181399 | 2413274 | -24.062% |

## Registered deviations

```json
{
  "all_zero_cross_dso": [
    {
      "allowed": true,
      "case": "all_zero",
      "dsos": [
        "libavcodec",
        "libavutil"
      ],
      "hash": "0x0209aa3e1d398548",
      "name": "ff_scalarproduct_float_c",
      "nonzero_dsos": [],
      "sources": [
        {
          "build_id": "6f2941ecf082a95809bcf8d8a6bc4888dbdaccac",
          "counts": [
            0,
            0
          ],
          "dso": "libavutil",
          "run": "pgo-train-1"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-1"
        },
        {
          "build_id": "6f2941ecf082a95809bcf8d8a6bc4888dbdaccac",
          "counts": [
            0,
            0
          ],
          "dso": "libavutil",
          "run": "pgo-train-2"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-2"
        },
        {
          "build_id": "6f2941ecf082a95809bcf8d8a6bc4888dbdaccac",
          "counts": [
            0,
            0
          ],
          "dso": "libavutil",
          "run": "pgo-train-3"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-3"
        }
      ]
    },
    {
      "allowed": true,
      "case": "all_zero",
      "dsos": [
        "libavcodec",
        "libavutil"
      ],
      "hash": "0x02dab88d7de0936e",
      "name": "ff_timecode_set_smpte",
      "nonzero_dsos": [],
      "sources": [
        {
          "build_id": "6f2941ecf082a95809bcf8d8a6bc4888dbdaccac",
          "counts": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavutil",
          "run": "pgo-train-1"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-1"
        },
        {
          "build_id": "6f2941ecf082a95809bcf8d8a6bc4888dbdaccac",
          "counts": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavutil",
          "run": "pgo-train-2"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-2"
        },
        {
          "build_id": "6f2941ecf082a95809bcf8d8a6bc4888dbdaccac",
          "counts": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavutil",
          "run": "pgo-train-3"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-3"
        }
      ]
    },
    {
      "allowed": true,
      "case": "all_zero",
      "dsos": [
        "libavcodec",
        "libavformat.so.62.3.100"
      ],
      "hash": "0x0d55ab714fffffff",
      "name": "ff_toupper4",
      "nonzero_dsos": [],
      "sources": [
        {
          "build_id": "7c415dce16ddc504948ce65ebcf5c1678a3d7a6d",
          "counts": [
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavformat.so.62.3.100",
          "run": "pgo-train-1"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-1"
        },
        {
          "build_id": "7c415dce16ddc504948ce65ebcf5c1678a3d7a6d",
          "counts": [
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavformat.so.62.3.100",
          "run": "pgo-train-2"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-2"
        },
        {
          "build_id": "7c415dce16ddc504948ce65ebcf5c1678a3d7a6d",
          "counts": [
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavformat.so.62.3.100",
          "run": "pgo-train-3"
        },
        {
          "build_id": "529bd3535847785bc306295fdf93600d78165231",
          "counts": [
            0,
            0,
            0,
            0,
            0
          ],
          "dso": "libavcodec",
          "run": "pgo-train-3"
        }
      ]
    }
  ],
  "compiler_rt": {
    "applies_to": [
      "PGOGEN"
    ],
    "evr": "22.1.8-1.6",
    "installed_record": "compiler-rt-22.1.8-1.6.aarch64 0f3895e319994ee53e5a82370c477ffb90e5cb295aabe6512682fce634634f1b",
    "original_sha256": "396c1e890736844acb981cb52f1a044d945022bcd8170d5ca6f5b538af9c7981",
    "package": "compiler-rt-22.1.8-1.6.aarch64.rpm",
    "sha256": "bd8dd2dee4139910cede020736c9eff3b90619bd1e63a724de98b72f4aa875be",
    "snapshot": "tizen-base-toolchain_20261119.042539",
    "tier": 2,
    "url": "https://download.tizen.org/snapshots/TIZEN/Tizen/Tizen-Base-Toolchain/tizen-base-toolchain_20261119.042539/repos/standard/packages/aarch64/compiler-rt-22.1.8-1.6.aarch64.rpm",
    "verification_path": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-runtime-source-20261125/raw-version-proof.json",
    "verification_sha256": "e9e0857ee31b4d6dd804849abdbd616b660503be3fb081e46dcb7470d36b9a1a"
  },
  "s5_archived_rebuilds": {
    "AFDO": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-s5-board-20261126/verified-builds/AFDO/revalidated.json",
    "BASE-r": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-s5-board-20261126/verified-builds/BASE-r/revalidated.json",
    "PGO": "/home/linhao/Toolchain/development/llvm_autofdo_bolt_agent/temp/m2b-s5-board-20261126/verified-builds/PGO/revalidated.json"
  }
}
```
