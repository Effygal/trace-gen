#include <stdio.h>
#include <vector>
#include <set>
#include <unordered_set>
#include <stdint.h>

class clock1
{
	int C = 0;
	std::vector<int> cache;
	std::vector<int> t_enter;
	std::vector<int> abit;
	std::vector<char> map;

	std::vector<int> enter; // time item entered cache
	std::vector<int> ref;	// time item last referenced
	std::vector<int> top;	// most recent time at top of cache

	int n_top = 0;
	double sum_top = 0, sum_top2 = 0;

	int ptr = 0, len = 0;
	int in = 0, out = 0;

	int64_t n_cachefill = 0;
	int64_t n_access = 0;
	int64_t n_miss = 0;
	int64_t n_recycle = 0;
	int64_t n_examined = 0;
	int64_t sum_abit = 0;

public:
	clock1(int _C)
	{
		C = _C;
		cache.resize(C + 1);
		t_enter.resize(C + 1);
		map.resize(100000, 0);
		abit.resize(100000, 0);
	}

	bool full(void)
	{
		return (in + 1) % (C + 1) == out;
	}

	int pop(void)
	{
		int addr = cache[out];
		int64_t age = (n_access - t_enter[out]);
		out = (out + 1) % (C + 1);
		map[addr] = false;
		sum_top += age;
		sum_top2 += (age * age);
		n_top++;
		return addr;
	}

	void push(int addr)
	{
		cache[in] = addr;
		t_enter[in] = n_access;
		in = (in + 1) % (C + 1);
		map[addr] = true;
		abit[addr] = false;
	}

	// must have enough space for C entries
	int contents(int *val)
	{
		int i, n;
		for (i = (in + C) % (C + 1), n = 0;; i = (i + C) % (C + 1))
		{
			val[n++] = cache[i];
			if (i == out)
				break;
		}
		return n;
	}

	void access(int addr)
	{
		n_access++;
		if (addr >= map.size())
		{
			int n = addr * 3 / 2;
			map.resize(n, 0); // like, resize to n, and append 0 to the vector.
			abit.resize(n, 0);
		}

		if (!map[addr])
		{
			n_miss++;
			if (!full())
				n_cachefill = n_access;
			else
			{
				while (true)
				{
					int evictee = pop();
					n_examined++;
					if (abit[evictee])
					{
						sum_abit += abit[evictee];
						abit[evictee] = 0;
						push(evictee);
						n_recycle++;
					}
					else
						break;
				}
			}
			push(addr);
		}
		else
			abit[addr] += 1;
	}

	void access_verbose(int addr, int *evict_addr, int *miss,
						int *ref_age, int *enter_age)
	{
		n_access++;
		if (addr >= map.size())
		{
			int n = addr * 3 / 2;
			map.resize(n, 0);
			abit.resize(n, 0);
			enter.resize(n, 0);
			ref.resize(n, 0);
		}

		if (!map[addr])
		{
			n_miss++;
			if (!full())
				n_cachefill = n_access;
			else
			{
				while (true)
				{
					int evictee = pop();
					if (abit[evictee])
					{
						abit[evictee] = false;
						push(evictee);
						n_recycle++;
					}
					else
					{
						if (miss)
						{
							*miss = 1;
							*evict_addr = evictee;
							*ref_age = n_access - ref[evictee];
							*enter_age = n_access - enter[evictee];
						}
						break;
					}
				}
			}
			push(addr);
			enter[addr] = ref[addr] = n_access;
		}
		else
		{
			abit[addr] = true;
			ref[addr] = n_access;
		}
	}

	void multi_access(int n, int *addrs)
	{
		for (int i = 0; i < n; i++)
			access(addrs[i]);
	}

	void queue_stats(int *n, double *sum, double *sum2)
	{
		*n = n_top;
		*sum = sum_top;
		*sum2 = sum_top2;
	}

	void multi_access_age(int n, int *addrs, int *evicted, int *misses,
						  int *age1, int *age2)
	{
		enter.resize(100000);
		ref.resize(100000);
		top.resize(100000);
		for (int i = 0; i < n; i++)
			access_verbose(addrs[i], &evicted[i], &misses[i], &age1[i], &age2[i]);
	}

	double hit_rate(void)
	{
		double miss_rate = (n_miss - C) * 1.0 / (n_access - n_cachefill);
		return 1 - miss_rate;
	}

	void data(int &_access, int &_miss, int &_cachefill, int &_recycle,
			  int &_examined, int &_sum_abit)
	{
		_access = n_access;
		_miss = n_miss;
		_cachefill = n_cachefill;
		_recycle = n_recycle;
		_examined = n_examined;
		_sum_abit = sum_abit;
	}
};

extern "C" void *clock1_create(int C)
{
	clock1 *f = new clock1(C);
	return (void *)f;
}

extern "C" void clock1_delete(void *_f)
{
	clock1 *f = (clock1 *)_f;
	delete f;
}

extern "C" void clock1_run(void *_f, int n, int *a)
{
	clock1 *f = (clock1 *)_f;
	f->multi_access(n, a); // n = trace length; a = start of the trace.
}

extern "C" int clock1_contents(void *_f, int *out)
{
	clock1 *f = (clock1 *)_f;
	return f->contents(out);
}

extern "C" void clock1_run_age(void *_f, int n, int *a, int *b, int *c, int *d, int *e)
{
	clock1 *f = (clock1 *)_f;
	f->multi_access_age(n, a, b, c, d, e);
}

extern "C" void clock1_queue_stats(void *_f, int *n, double *sum, double *sum2)
{
	clock1 *f = (clock1 *)_f;
	f->queue_stats(n, sum, sum2);
}

extern "C" double clock1_hitrate(void *_f)
{
	clock1 *f = (clock1 *)_f;
	return f->hit_rate();
}

extern "C" void clock1_data(void *_f, int *_access, int *_miss,
							int *_cachefill, int *_recycle,
							int *_examined, int *_sum_abit)
{
	clock1 *f = (clock1 *)_f;
	f->data(*_access, *_miss, *_cachefill, *_recycle, *_examined, *_sum_abit);
}
