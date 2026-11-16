command() { printf "<%s>\n" "$@"; }

ninja() { command /usr/bin/ninja -j2 "$@"; }; export CMAKE_BUILD_PARALLEL_LEVEL=2
ninja bolt bolt_rt
ninja install
ninja "space arg" ""
