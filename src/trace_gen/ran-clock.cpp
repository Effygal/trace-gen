#include <stdio.h>
#include <vector>
#include <set>
#include <unordered_set>
#include <algorithm>
#include <stdint.h>
#include <random>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class ran_clock
{
	int C = 0;
	std::vector<int> cache;
	std::vector<int> t_enter;
	std::vector<int> abit;
	std::vector<char> map;

	std::vector<int> enter; // time item entered cache
	std::vector<int> ref;	// time item last referenced
	
	int n_top = 0;
	double sum_top = 0, sum_top2 = 0;

	int in = 0, out = 0;

	int n_cachefill = 0;
	int n_access = 0;
	int n_miss = 0;
	int n_recycle = 0;
	int n_examined = 0;
	int sum_abit = 0;

	std::mt19937 rng;
	int in_ptr = -1;

public:
	ran_clock(int _C) : rng(std::random_device{}())
	{
		C = _C;
		cache.resize(C + 1);
		t_enter.resize(C + 1);
		map.resize(100000, 0);
		abit.resize(100000, 0);
	}
	~ran_clock() {}

	bool full(void)
	{
		return (in + 1) % (C + 1) == out;
	}

	int pop(void)
	{
		if (C == 0)
			return -1;
		std::uniform_int_distribution<int> dist(0, C - 1);
		while (true)
		{
			int offset = dist(rng);
			int slot = (out + offset) % (C + 1);
			int32_t addr = cache[slot];
			n_examined++;
			if (abit[addr])
			{
				sum_abit += abit[addr];
				abit[addr] = 0;
				n_recycle++;
			}
			else
			{
				int age = (n_access - t_enter[slot]);
				sum_top += age;
				sum_top2 += (age * age);
				n_top++;
				map[addr] = false;
				in_ptr = slot;
				return addr;
			}
		}
	}

	int pop_no_rp(void)
	{
		if (C == 0)
			return -1;
		std::vector<int> offsets(C);
		for (int i = 0; i < C; i++)
			offsets[i] = i;
		std::shuffle(offsets.begin(), offsets.end(), rng);

		int fallback_slot = -1;
		int32_t fallback_addr = -1;

		for (int idx = 0; idx < C; idx++)
		{
			int slot = (out + offsets[idx]) % (C + 1);
			int32_t addr = cache[slot];
			n_examined++;
			if (abit[addr])
			{
				sum_abit += abit[addr];
				abit[addr] = 0;
				n_recycle++;
				if (fallback_slot == -1)
				{
					fallback_slot = slot;
					fallback_addr = addr;
				}
				continue;
			}

			int age = (n_access - t_enter[slot]);
			sum_top += age;
			sum_top2 += (age * age);
			n_top++;
			map[addr] = false;
			in_ptr = slot;
			return addr;
		}

		// All had abit set; evict the first one we touched after clearing bits.
		int age = (n_access - t_enter[fallback_slot]);
		sum_top += age;
		sum_top2 += (age * age);
		n_top++;
		map[fallback_addr] = false;
		in_ptr = fallback_slot;
		return fallback_addr;
	}

	void push(int32_t addr)
	{
		int slot = (in_ptr != -1) ? in_ptr : in;
		cache[slot] = addr;
		t_enter[slot] = n_access;
		if (in_ptr == -1)
			in = (in + 1) % (C + 1);
		else
			in_ptr = -1;
		map[addr] = true;
		abit[addr] = false;
	}

	int contents(py::array_t< int >& val)
	{
		int* val_ptr = val.mutable_data();
		int i, n;
		for (i = (in + C) % (C + 1), n = 0;; i = (i + C) % (C + 1))
		{
			val_ptr[n++] = cache[i];
			if (i == out)
				break;
		}
		return n;
	}

	void access(int32_t addr)
	{
		n_access++;
		if (addr >= map.size())
		{
			int n = addr * 3 / 2;
			map.resize(n, 0); 
			abit.resize(n, 0);
		}

		if (!map[addr])
		{
			n_miss++;
			if (!full())
			{
				n_cachefill = n_access;
				push(addr);
			}
			else
			{
				// int evictee = pop();
				int evictee = pop_no_rp();
				if (evictee == -1)
					return;
				push(addr);
			}
		}
		else
			abit[addr] += 1;
	}

	void access_no_rp(int32_t addr)
	{
		n_access++;
		if (addr >= map.size())
		{
			int n = addr * 3 / 2;
			map.resize(n, 0); 
			abit.resize(n, 0);
		}

		if (!map[addr])
		{
			n_miss++;
			if (!full())
			{
				n_cachefill = n_access;
				push(addr);
			}
			else
			{
				int evictee = pop_no_rp();
				if (evictee == -1)
					return;
				push(addr);
			}
		}
		else
			abit[addr] += 1;
	}

	void access_verbose(int32_t addr, int32_t* evict_addr, int* miss,
						int* ref_age, int* enter_age)
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
			{
				n_cachefill = n_access;
				push(addr);
				enter[addr] = ref[addr] = n_access;
			}
			else
			{
				// int evictee = pop();
				int evictee = pop_no_rp();
				if (evictee == -1)
					return;
				if (miss)
				{
					*miss = 1;
					*evict_addr = evictee;
					*ref_age = n_access - ref[evictee];
					*enter_age = n_access - enter[evictee];
				}
				push(addr);
				enter[addr] = ref[addr] = n_access;
			}
		}
		else
		{
			abit[addr] = true;
			ref[addr] = n_access;
		}
	}

	void access_verbose_no_rp(int32_t addr, int32_t* evict_addr, int* miss,
						int* ref_age, int* enter_age)
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
			{
				n_cachefill = n_access;
				push(addr);
				enter[addr] = ref[addr] = n_access;
			}
			else
			{
				int evictee = pop_no_rp();
				if (evictee == -1)
					return;
				if (miss)
				{
					*miss = 1;
					*evict_addr = evictee;
					*ref_age = n_access - ref[evictee];
					*enter_age = n_access - enter[evictee];
				}
				push(addr);
				enter[addr] = ref[addr] = n_access;
			}
		}
		else
		{
			abit[addr] = true;
			ref[addr] = n_access;
		}
	}

	void multi_access(int n, py::array_t< int32_t >& addrs)
	{
		int32_t* addrs_ptr = addrs.mutable_data();
		for (int i = 0; i < n; i++)
			access(addrs_ptr[i]);
	}

	void multi_access_no_rp(int n, py::array_t< int32_t >& addrs)
	{
		int32_t* addrs_ptr = addrs.mutable_data();
		for (int i = 0; i < n; i++)
			access_no_rp(addrs_ptr[i]);
	}

	void queue_stats(py::array_t< int >& n, py::array_t<double>& sum, py::array_t<double>& sum2)
	{
		int* n_ptr = n.mutable_data();
		double* sum_ptr = sum.mutable_data();
		double* sum2_ptr = sum2.mutable_data();
		*n_ptr = n_top;
		*sum_ptr = sum_top;
		*sum2_ptr = sum_top2;
	}

	void multi_access_age(int n, py::array_t< int32_t >& addrs, py::array_t< int >& evicted, py::array_t< int >& misses,
						  py::array_t< int >& age1, py::array_t< int >& age2)
	{
		int32_t* addrs_ptr = addrs.mutable_data();
		int* evicted_ptr = evicted.mutable_data();
		int* misses_ptr = misses.mutable_data();
		int* age1_ptr = age1.mutable_data();
		int* age2_ptr = age2.mutable_data();

		enter.resize(100000);
		ref.resize(100000);
		
		for (int i = 0; i < n; i++)
			access_verbose(addrs_ptr[i], &evicted_ptr[i], &misses_ptr[i], &age1_ptr[i], &age2_ptr[i]);
	}

	void multi_access_age_no_rp(int n, py::array_t< int32_t >& addrs, py::array_t< int >& evicted, py::array_t< int >& misses,
						  py::array_t< int >& age1, py::array_t< int >& age2)
	{
		int32_t* addrs_ptr = addrs.mutable_data();
		int* evicted_ptr = evicted.mutable_data();
		int* misses_ptr = misses.mutable_data();
		int* age1_ptr = age1.mutable_data();
		int* age2_ptr = age2.mutable_data();

		enter.resize(100000);
		ref.resize(100000);
		
		for (int i = 0; i < n; i++)
			access_verbose_no_rp(addrs_ptr[i], &evicted_ptr[i], &misses_ptr[i], &age1_ptr[i], &age2_ptr[i]);
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

PYBIND11_MODULE(_ran_clock, m)
{
	py::class_<ran_clock>(m, "ran_clock")
		.def(py::init<int>())
		.def("multi_access", &ran_clock::multi_access)
		.def("multi_access_no_rp", &ran_clock::multi_access_no_rp)
		.def("contents", &ran_clock::contents)
		.def("multi_access_age", &ran_clock::multi_access_age)
		.def("multi_access_age_no_rp", &ran_clock::multi_access_age_no_rp)
		.def("queue_stats", &ran_clock::queue_stats)
		.def("hit_rate", &ran_clock::hit_rate)
		.def("data", &ran_clock::data);
	m.def("ran_clock_create", [](int C) {
		return new ran_clock(C);
	});
	m.def("ran_clock_run", [](void* _c, int n, py::array_t< int32_t >& a) {
		ran_clock* c = (ran_clock *)_c;
		c->multi_access(n, a);
	});
	m.def("ran_clock_run_no_rp", [](void* _c, int n, py::array_t< int32_t >& a) {
		ran_clock* c = (ran_clock *)_c;
		c->multi_access_no_rp(n, a);
	});
	m.def("ran_clock_contents", [](void* _c, py::array_t< int >& out) {
		ran_clock* c = (ran_clock *)_c;
		return c->contents(out);
	});
	m.def("ran_clock_run_age", [](void* _c, int n, py::array_t< int32_t >& a, py::array_t< int >& b, py::array_t< int >& c, py::array_t< int >& d, py::array_t< int >& e) {
		ran_clock* cl = (ran_clock *)_c;
		cl->multi_access_age(n, a, b, c, d, e);
	});
	m.def("ran_clock_run_age_no_rp", [](void* _c, int n, py::array_t< int32_t >& a, py::array_t< int >& b, py::array_t< int >& c, py::array_t< int >& d, py::array_t< int >& e) {
		ran_clock* cl = (ran_clock *)_c;
		cl->multi_access_age_no_rp(n, a, b, c, d, e);
	});
	m.def("ran_clock_queue_stats", [](void* _c, py::array_t< int >& n, py::array_t< double >& sum, py::array_t< double >& sum2) {
		ran_clock* c = (ran_clock *)_c;
		c->queue_stats(n, sum, sum2);
	});
	m.def("ran_clock_hitrate", [](void* _c) {
		ran_clock* c = (ran_clock *)_c;
		return c->hit_rate();
	});
	m.def("ran_clock_data", [](py::object _c) -> py::tuple {
		if (py::isinstance<ran_clock>(_c))
		{
			ran_clock cl = _c.cast<ran_clock>();
			int _access, _miss, _cachefill, _recycle, _examined, _sum_abit;
			cl.data(_access, _miss, _cachefill, _recycle, _examined, _sum_abit);
			return py::make_tuple(_access, _miss, _cachefill, _recycle, _examined, _sum_abit);
		} else {
			throw std::invalid_argument("Not passing ran_clock object");
		}
	});
}
