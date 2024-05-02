#include <stdio.h>
#include <vector>
#include <queue>
#include <map>

class clock3
{
	int C = 0;
	std::queue<int> cache;
	std::map<int, bool> map;
	std::map<int, bool> abit;

	int64_t n_cachefill = 0;
	int64_t n_access = 0;
	int64_t n_miss = 0;
	int64_t n_recycle = 0;

public:
	clock3(int _C)
	{
		C = _C;
	}

	void access(int addr)
	{
		n_access++;

		auto it = map.find(addr);
		if (it == map.end() || !map[addr])
		{
			n_miss++;
			if (cache.size() < C)
				n_cachefill = n_access;
			else
			{
				while (true)
				{
					int evictee = cache.front();
					cache.pop();
					if (abit[evictee])
					{
						abit[evictee] = false;
						cache.push(evictee);
						n_recycle++;
					}
					else
					{
						map[evictee] = false;
						break;
					}
				}
			}
			cache.push(addr);
			map[addr] = true;
			abit[addr] = false;
		}
		else
			abit[addr] = true;
	}

	void multi_access(int n, int *addrs)
	{
		for (int i = 0; i < n; i++)
			access(addrs[i]);
	}

#if 0
    void multi_access_verbose(int n, int *addrs, int *misses) {
	for (int i = 0; i < n; i++) {
	    
	    int nm = n_miss;
	    access(addrs[i]);
	    if (n_miss != nm)
		misses[i] = 1;
	}
    }

    void multi_access_age(int n, int *addrs, int *misses, int *age) {
	std::vector<int> times;
	times.resize(C, 0);
	int t = 1;
	for (int i = 0; i < n; i++, t++) {
	    n_access++;
	    auto addr = addrs[i];
	    if (addr >= map.size())
		map.resize(addr * 3 / 2, 0);
	    if (!map[addr]) {
		n_miss++;
		misses[i] = 1;
		if ((in + 1) % (C + 1) != out) { // cache not full
		    n_cachefill = n_access;
		}
		else {
		    int evictee = cache[out];
		    age[i] = t - times[out];
		    out = (out + 1) % (C + 1);
		    map[evictee] = false;
		}
		cache[in] = addr;
		times[in] = t;
		map[addr] = true;
		in = (in + 1) % (C + 1);
	    }
	}
    }
#endif

	double hit_rate(void)
	{
		double miss_rate = (n_miss - C) * 1.0 / (n_access - n_cachefill);
		return 1 - miss_rate;
	}

	void data(int *_access, int *_miss, int *_cachefill, int *_recycle)
	{
		*_access = n_access;
		*_miss = n_miss;
		*_cachefill = n_cachefill;
		*_recycle = n_recycle;
	}
};

extern "C" void *clock_create(int C)
{
	clock3 *f = new clock3(C);
	return (void *)f;
}

extern "C" void clock_delete(void *_f)
{
	clock3 *f = (clock3 *)_f;
	delete f;
}

extern "C" void clock_run(void *_f, int n, int *a)
{
	clock3 *f = (clock3 *)_f;
	f->multi_access(n, a);
}

#if 0
extern "C" void clock_run_verbose(void *_f, int n, int *a, int *b)
{
    clock *f = (clock*) _f;
    f->multi_access_verbose(n, a, b);
}

extern "C" void clock_run_age(void *_f, int n, int *a, int *b, int *c)
{
    clock *f = (clock*) _f;
    f->multi_access_age(n, a, b, c);
}
#endif

extern "C" double clock_hitrate(void *_f)
{
	clock3 *f = (clock3 *)_f;
	return f->hit_rate();
}

extern "C" void clock_data(void *_f, int *_access, int *_miss,
						   int *_cachefill, int *_recycle)
{
	clock3 *f = (clock3 *)_f;
	f->data(_access, _miss, _cachefill, _recycle);
}
