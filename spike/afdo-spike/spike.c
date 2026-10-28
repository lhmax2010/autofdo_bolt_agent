/* Deterministic profile-guided optimization feasibility workload.
 * No elapsed-time loop: all variants must execute identical work.
 * Usage: afdo-spike-{base,instr,pgo,afdo} [rounds] [seed]
 * Unsigned arithmetic makes wraparound intentional and defined.
 */
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BLOCK_SIZE 128u
#define TABLE_SIZE 4096u
#define DEFAULT_ROUNDS 100000u
#define DEFAULT_SEED UINT64_C(0x123456789abcdef)
#define NOINLINE __attribute__((noinline))

struct entry {
    uint32_t key;
    uint32_t value;
};

static struct entry table[TABLE_SIZE];
static uint64_t initial_seed;

/* Fixed PRNG, independent of libc and platform word size. */
static uint64_t next_random(uint64_t *state)
{
    uint64_t x = *state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *state = x;
    return x * UINT64_C(2685821657736338717);
}

static uint64_t rotate_left(uint64_t x, unsigned int shift)
{
    return (x << shift) | (x >> (64u - shift));
}

/* A named hot function, retained for profile inspection. */
NOINLINE uint64_t hash_mix(uint64_t x)
{
    x ^= x >> 30;
    x *= UINT64_C(0xbf58476d1ce4e5b9);
    x ^= x >> 27;
    x *= UINT64_C(0x94d049bb133111eb);
    return x ^ (x >> 31);
}

static void initialize_table(void)
{
    uint64_t state = initial_seed;
    for (uint32_t i = 0; i < TABLE_SIZE; ++i) {
        table[i].key = (uint32_t)next_random(&state);
        table[i].value = (uint32_t)hash_mix(table[i].key);
    }
}

/* Ordinary insertion sort gives biased comparisons and a clear hotspot. */
NOINLINE void sort_block(uint32_t *values, unsigned int count)
{
    for (unsigned int i = 1; i < count; ++i) {
        uint32_t value = values[i];
        unsigned int j = i;
        while (j != 0 && values[j - 1] > value) {
            values[j] = values[j - 1];
            --j;
        }
        values[j] = value;
    }
}

/* Repeated table lookups exercise data-dependent integer arithmetic. */
NOINLINE uint64_t lookup_work(const uint32_t *values, uint64_t state)
{
    uint64_t sum = 0;
    for (unsigned int i = 0; i < BLOCK_SIZE; ++i) {
        uint32_t key = values[i];
        uint32_t index = (key ^ (key >> 13)) & (TABLE_SIZE - 1);
        const struct entry *item = &table[index];
        uint64_t mixed = ((uint64_t)item->key << 32) | item->value;
        if ((key & 15u) != 0) {
            sum += hash_mix(mixed ^ state ^ key);
        } else {
            sum ^= rotate_left(mixed + key, 17);
        }
        state = rotate_left(state + sum + i, 11);
    }
    return sum ^ state;
}

/* Invoked only once per 1024 rounds. No explicit cold/hot hints. */
NOINLINE uint64_t rare_path(uint64_t value)
{
    for (unsigned int i = 0; i < 31; ++i) {
        if ((value & 7u) == 3u) {
            value = hash_mix(value + i);
        } else {
            value = rotate_left(value, 9) ^ UINT64_C(0xd6e8feb86659fd93);
        }
    }
    return value;
}

static uint64_t checksum_block(const uint32_t *values)
{
    uint64_t sum = 0;
    for (unsigned int i = 0; i < BLOCK_SIZE; ++i) {
        sum += (uint64_t)values[i] * (i + 1u);
    }
    return sum;
}

NOINLINE uint64_t run_workload(uint64_t rounds)
{
    uint32_t values[BLOCK_SIZE];
    uint64_t random_state = initial_seed;
    uint64_t checksum = UINT64_C(0x6a09e667f3bcc909);
    for (uint64_t round = 0; round < rounds; ++round) {
        for (unsigned int i = 0; i < BLOCK_SIZE; ++i) {
            values[i] = (uint32_t)next_random(&random_state);
        }
        sort_block(values, BLOCK_SIZE);
        checksum += checksum_block(values);
        checksum ^= lookup_work(values, random_state);
        if ((round & 1023u) == 0) {
            checksum ^= rare_path(checksum);
        } else {
            checksum = rotate_left(checksum, 13) + round;
        }
    }
    return checksum;
}

static int parse_number(const char *text, uint64_t *value)
{
    char *end = NULL;
    unsigned long long parsed;
    if (text[0] == '-' || text[0] == '\0') {
        return 0;
    }
    errno = 0;
    parsed = strtoull(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0' || parsed == 0) {
        return 0;
    }
    *value = (uint64_t)parsed;
    return 1;
}

int main(int argc, char **argv)
{
    uint64_t rounds = DEFAULT_ROUNDS;
    uint64_t seed = DEFAULT_SEED;
    uint64_t result;
    if (argc > 3 || (argc > 1 && !parse_number(argv[1], &rounds)) ||
        (argc > 2 && !parse_number(argv[2], &seed))) {
        fprintf(stderr, "usage: %s [positive-rounds] [positive-seed]\n", argv[0]);
        return 2;
    }
    /* Bound accidental invocations while still allowing long measurements. */
    if (rounds > UINT64_C(1000000000)) {
        fprintf(stderr, "rounds exceeds 1000000000\n");
        return 2;
    }
    initial_seed = seed;
    initialize_table();
    result = run_workload(rounds);
    printf("rounds=%" PRIu64 " seed=%016" PRIx64 " checksum=%016" PRIx64 "\n",
           rounds, seed, result);
    return 0;
}
