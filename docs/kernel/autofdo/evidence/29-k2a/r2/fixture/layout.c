/* Two branch regimes for checking GCOV to sample-profile consumption. */
volatile unsigned sink;

__attribute__((noinline)) int left(int x);
__attribute__((noinline)) int right(int x);

__attribute__((noinline)) int choose(int x)
{
    if (x == 0) {
        int v = left(x);
        sink = sink * 3u + (unsigned)v;
        return v;
    }
    int v = right(x);
    sink = sink * 5u + (unsigned)v;
    return v;
}

__attribute__((noinline)) int left(int x)
{
    return (int)((unsigned)x * 7u + sink % 13u);
}

__attribute__((noinline)) int right(int x)
{
    return (int)((unsigned)x * 11u + sink % 19u);
}

int main(int argc, char **argv)
{
    (void)argv;
    const int reverse = argc > 1;
    for (int i = 0; i < 100000; ++i) {
        const int rare = i % 1000 == 0;
        choose(reverse ? !rare : rare);
    }
    return sink == 0x12345678u;
}
