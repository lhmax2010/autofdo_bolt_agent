__attribute__((no_profile_instrument_function, section(".noinstr.text"), noinline))
int early(int x)
{
    return x > 6 ? x - 4 : x + 3;
}

int ordinary(int x)
{
    if (x > 6)
        return early(x);
    return x + 3;
}
