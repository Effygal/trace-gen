#include <stdio.h>
#include <vector>
#include <set>
#include <unordered_set>
#include <stdint.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

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

	int n_cachefill = 0;
	int n_access = 0;
	int n_miss = 0;
	int n_recycle = 0;
	int n_examined = 0;
	int sum_abit = 0;

public:
	clock1(int _C)
	{
		C = _C;
		cache.resize(C + 1);
		t_enter.resize(C + 1);
		map.resize(100000, 0);
		abit.resize(100000, 0);
	}
	~clock1() {}

	bool full(void)
	{
		return (in + 1) % (C + 1) == out;
	}

	int pop(void)
	{
		int32_t addr = cache[out];
		int age = (n_access - t_enter[out]);
		out = (out + 1) % (C + 1);
		map[addr] = false;
		sum_top += age;
		sum_top2 += (age * age);
		n_top++;
		return addr;
	}

	void push(int32_t addr)
	{
		cache[in] = addr;
		t_enter[in] = n_access;
		in = (in + 1) % (C + 1);
		map[addr] = true;
		abit[addr] = false;
	}

	// must have enough space for C entries
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

	void multi_access(int n, py::array_t< int32_t >& addrs)
	{
		int32_t* addrs_ptr = addrs.mutable_data();
		for (int i = 0; i < n; i++)
			access(addrs_ptr[i]);
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
		top.resize(100000);
		for (int i = 0; i < n; i++)
			access_verbose(addrs_ptr[i], &evicted_ptr[i], &misses_ptr[i], &age1_ptr[i], &age2_ptr[i]);
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

PYBIND11_MODULE(_clock, m)
{
	py::class_<clock1>(m, "clock1")
		.def(py::init<int>())
		.def("multi_access", &clock1::multi_access)
		.def("contents", &clock1::contents)
		.def("multi_access_age", &clock1::multi_access_age)
		.def("queue_stats", &clock1::queue_stats)
		.def("hit_rate", &clock1::hit_rate)
		.def("data", &clock1::data);
	m.def("clock1_create", [](int C) {
		return new clock1(C);
	});
	m.def("clock1_run", [](void* _c, int n, py::array_t< int32_t >& a) {
		clock1* c = (clock1 *)_c;
		c->multi_access(n, a);
	});
	m.def("clock1_contents", [](void* _c, py::array_t< int >& out) {
		clock1* c = (clock1 *)_c;
		return c->contents(out);
	});
	m.def("clock1_run_age", [](void* _c, int n, py::array_t< int32_t >& a, py::array_t< int >& b, py::array_t< int >& c, py::array_t< int >& d, py::array_t< int >& e) {
		clock1* cl = (clock1 *)_c;
		cl->multi_access_age(n, a, b, c, d, e);
	});
	m.def("clock1_queue_stats", [](void* _c, py::array_t< int >& n, py::array_t< double >& sum, py::array_t< double >& sum2) {
		clock1* c = (clock1 *)_c;
		c->queue_stats(n, sum, sum2);
	});
	m.def("clock1_hitrate", [](void* _c) {
		clock1* c = (clock1 *)_c;
		return c->hit_rate();
	});
	m.def("clock1_data", [](py::object _c) -> py::tuple {
		if (py::isinstance<clock1>(_c))
		{
			clock1 cl = _c.cast<clock1>();
			int _access, _miss, _cachefill, _recycle, _examined, _sum_abit;
			cl.data(_access, _miss, _cachefill, _recycle, _examined, _sum_abit);
			return py::make_tuple(_access, _miss, _cachefill, _recycle, _examined, _sum_abit);
		} else {
			throw std::invalid_argument("Not passing clock1 object");
		}
	});
}
