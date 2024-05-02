#include <stdlib.h>
#include <stdint.h>

double fifo(int M, int C, int n, int32_t *a)
{
    int X = C + 1;
    int32_t *cache = calloc(1, sizeof(int32_t) * X);
    int in = 0, out = 0;
    char *_m = calloc(1, M);
    int hits = 0, misses = 0;

    for (int i = 0; i < n; i++)
    {
        int _a = a[i];
        if (_m[_a])
            hits++;
        else
        {
            misses++;
            if ((in + 1) % X != out)
            {
                cache[in] = _a;
                _m[_a] = 1;
                in = (in + 1) % X;
            }
            else
            {
                int b = cache[out];
                out = (out + 1) % X;
                _m[b] = 0;
                cache[in] = _a;
                _m[_a] = 1;
                in = (in + 1) % X;
            }
        }
    }
    return (1.0 * hits) / (hits + misses);
}
