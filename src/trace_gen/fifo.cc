#include <stdio.h>
#include <vector>
#include <set>
#include <unordered_set>
#include <assert.h>

class fifo
{
	int C = 0;
	std::vector<int> cache;
	std::vector<int> enter;

	int n_evict = 0;
	double s_evict = 0;
	double s2_evict = 0;

	// std::unordered_set<int> map;
	//    std::set<int> map;
	std::vector<char> map;

	int64_t in = 0, out = 0;
	int64_t n_cachefill = 0;
	int64_t n_access = 0;
	int64_t n_miss = 0;

public:
	fifo(int _C)
	{
		C = _C;
		cache.resize(C + 1);
		enter.resize(C + 1, 0);
		map.resize(100000, 0);
	}

	void access(int addr)
	{
		n_access++;

		if (addr >= map.size())
			map.resize(addr * 3 / 2, 0);

		assert(addr < map.size());
		if (!map[addr])
		{
			n_miss++;
			if ((in + 1) % (C + 1) != out)
			{ // cache not full
				n_cachefill = n_access;
			}
			else
			{
				int evictee = cache[out];

				int age = n_access - enter[out];
				n_evict++;
				s_evict += age;
				s2_evict += 1.0 * age * age;

				out = (out + 1) % (C + 1);
				map[evictee] = false;
			}
			cache[in] = addr;
			enter[in] = n_access;
			map[addr] = true;
			in = (in + 1) % (C + 1);
		}
		assert(0 <= in && in < C + 1 && 0 <= out && out < C + 1);
	}

	// must have enough space for C entries
	int contents(int *val)
	{
		int i, n = 0;
		for (i = (in + C) % (C + 1);; i = (i + C) % (C + 1))
		{
			val[n++] = cache[i];
			if (i == out)
				break;
		}
		return n;
	}

	void multi_access(int n, int *addrs)
	{
		for (int i = 0; i < n; i++)
			access(addrs[i]);
	}

	void multi_access_verbose(int n, int *addrs, int *misses)
	{
		for (int i = 0; i < n; i++)
		{

			int nm = n_miss;
			access(addrs[i]);
			if (n_miss != nm)
				misses[i] = 1;
		}
	}

	void multi_access_age(int n, int *addrs, int *misses, int *age)
	{
		std::vector<int> times;
		times.resize(C, 0);
		int t = 1;
		for (int i = 0; i < n; i++, t++)
		{
			n_access++;
			auto addr = addrs[i];
			if (addr >= map.size())
				map.resize(addr * 3 / 2, 0);
			if (!map[addr])
			{
				n_miss++;
				misses[i] = 1;
				if ((in + 1) % (C + 1) != out)
				{ // cache not full
					n_cachefill = n_access;
				}
				else
				{
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

	double hit_rate(void)
	{
		double miss_rate = (n_miss - C) * 1.0 / (n_access - n_cachefill);
		return 1 - miss_rate;
	}

	void queue_stats(int *n, double *s, double *s2)
	{
		*n = n_evict;
		*s = s_evict;
		*s2 = s2_evict;
	}

	void data(int &_access, int &_miss, int &_cachefill)
	{
		_access = n_access;
		_miss = n_miss;
		_cachefill = n_cachefill;
	}
};

extern "C" void *fifo_create(int C)
{
	fifo *f = new fifo(C);
	return (void *)f;
}

extern "C" void fifo_delete(void *_f)
{
	fifo *f = (fifo *)_f;
	delete f;
}

extern "C" void fifo_run(void *_f, int n, int *a)
{
	fifo *f = (fifo *)_f;
	f->multi_access(n, a);
}

extern "C" int fifo_contents(void *_f, int *out)
{
	fifo *f = (fifo *)_f;
	f->contents(out);
}

extern "C" void fifo_run_verbose(void *_f, int n, int *a, int *b)
{
	fifo *f = (fifo *)_f;
	f->multi_access_verbose(n, a, b);
}

extern "C" void fifo_run_age(void *_f, int n, int *a, int *b, int *c)
{
	fifo *f = (fifo *)_f;
	f->multi_access_age(n, a, b, c);
}

extern "C" double fifo_hitrate(void *_f)
{
	fifo *f = (fifo *)_f;
	return f->hit_rate();
}

extern "C" void fifo_queue_stats(void *_f, int *n, double *s, double *s2)
{
	fifo *f = (fifo *)_f;
	f->queue_stats(n, s, s2);
}

extern "C" void fifo_data(void *_f, int *_access, int *_miss, int *_cachefill)
{
	fifo *f = (fifo *)_f;
	f->data(*_access, *_miss, *_cachefill);
}
