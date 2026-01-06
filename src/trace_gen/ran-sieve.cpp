#include <algorithm>
#include <list>
#include <random>
#include <stdint.h>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class ran_sieve
{
	int C = 0;
	int K = 1;
	std::vector<int> cache;
	std::vector<char> map;		  
	std::vector<int> counter;	   
	std::vector<int> t_enter;   
	std::vector<int> t_ref;	   
	int n_top = 0;
	double sum_top = 0, sum_top2 = 0;

	int n_cachefill = 0;
	int n_access = 0;
	int n_miss = 0;
	int n_recycle = 0;
	int n_examined = 0;
	int sum_counter = 0;

	std::mt19937 rng;

	void expand(int32_t addr)
	{
		if (addr >= static_cast<int32_t>(map.size()))
		{
			int n = addr * 3 / 2 + 1;
			map.resize(n, 0);
			counter.resize(n, 0);
			t_enter.resize(n, 0);
			t_ref.resize(n, 0);
		}
	}

	bool full(void)
	{
		return static_cast<int>(cache.size()) == C;
	}

	int pop(int* ref_age = nullptr, int* ent_age = nullptr)
	{
		if (cache.empty())
			return -1;

		std::uniform_int_distribution<int> dist(0, C - 1);
		while (true)
		{
			int idx = dist(rng);
			int addr = cache[idx];
			n_examined++;
			if (counter[addr] > 0)
			{
				sum_counter += counter[addr];
				counter[addr] -= 1;
				n_recycle++;
			}
			else
			{
				int r_age = n_access - t_ref[addr];
				int e_age = n_access - t_enter[addr];
				sum_top += e_age;
				sum_top2 += (e_age * e_age);
				n_top++;
				map[addr] = 0;
				counter[addr] = 0;
				cache[idx] = cache.back();
				cache.pop_back(); 
				if (ref_age)
					*ref_age = r_age;
				if (ent_age)
					*ent_age = e_age;
				return addr;
			}
		}
	}

	void push(int addr)
	{
		cache.push_back(addr);
		map[addr] = 1;
		counter[addr] = 0;
		t_enter[addr] = t_ref[addr] = n_access;
	}

public:
	ran_sieve(int _C, int _K = 1, uint32_t seed = 0) : C(_C), K(std::max(1, _K)), rng(seed ? seed : std::random_device{}())
	{
		map.resize(100000, 0);
		counter.resize(100000, 0);
		t_enter.resize(100000, 0);
		t_ref.resize(100000, 0);
		cache.reserve(C);
	}
	~ran_sieve() {}

	int contents(py::array_t< int >& val)
	{
		int* val_ptr = val.mutable_data();
		int n = 0;
		for (int addr : cache)
			val_ptr[n++] = addr;
		return n;
	}

	void access(int32_t addr)
	{
		n_access++;
		expand(addr);

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
				int evictee = pop();
				(void)evictee;
				push(addr);
			}
		}
		else
		{
			if (counter[addr] < K)
				counter[addr] += 1;
			t_ref[addr] = n_access;
		}
	}

	void access_verbose(int32_t addr, int32_t* evict_addr, int* miss,
						int* ref_age, int* enter_age)
	{
		if (evict_addr)
			*evict_addr = -1;
		if (miss)
			*miss = 0;
		if (ref_age)
			*ref_age = 0;
		if (enter_age)
			*enter_age = 0;

		n_access++;
		expand(addr);

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
				int r_age = 0, e_age = 0;
				int evictee = pop(&r_age, &e_age);
				if (evictee == -1)
					return;
				if (miss)
					*miss = 1;
				if (evict_addr)
					*evict_addr = evictee;
				if (ref_age)
					*ref_age = r_age;
				if (enter_age)
					*enter_age = e_age;
				push(addr);
			}
		}
		else
		{
			if (counter[addr] < K)
				counter[addr] += 1;
			t_ref[addr] = n_access;
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

		for (int i = 0; i < n; i++)
			access_verbose(addrs_ptr[i], &evicted_ptr[i], &misses_ptr[i], &age1_ptr[i], &age2_ptr[i]);
	}

	double hit_rate(void)
	{
		double miss_rate = (n_miss - C) * 1.0 / (n_access - n_cachefill);
		return 1 - miss_rate;
	}

	void data(int &_access, int &_miss, int &_cachefill, int &_recycle,
			  int &_examined, int &_sum_counter)
	{
		_access = n_access;
		_miss = n_miss;
		_cachefill = n_cachefill;
		_recycle = n_recycle;
		_examined = n_examined;
		_sum_counter = sum_counter;
	}
};

PYBIND11_MODULE(_ran_sieve, m)
{
	py::class_<ran_sieve>(m, "ran_sieve")
		.def(py::init<int, int, uint32_t>(), py::arg("C"), py::arg("K") = 1, py::arg("seed") = 0)
		.def("multi_access", &ran_sieve::multi_access)
		.def("contents", &ran_sieve::contents)
		.def("multi_access_age", &ran_sieve::multi_access_age)
		.def("queue_stats", &ran_sieve::queue_stats)
		.def("hit_rate", &ran_sieve::hit_rate)
		.def("data", &ran_sieve::data);
	m.def("ran_sieve_create", [](int C, int K, uint32_t seed) {
		return new ran_sieve(C, K, seed);
	}, py::arg("C"), py::arg("K") = 1, py::arg("seed") = 0);
	m.def("ran_sieve_run", [](void* _c, int n, py::array_t< int32_t >& a) {
		ran_sieve* c = (ran_sieve *)_c;
		c->multi_access(n, a);
	});
	m.def("ran_sieve_contents", [](void* _c, py::array_t< int >& out) {
		ran_sieve* c = (ran_sieve *)_c;
		return c->contents(out);
	});
	m.def("ran_sieve_run_age", [](void* _c, int n, py::array_t< int32_t >& a, py::array_t< int >& b, py::array_t< int >& c, py::array_t< int >& d, py::array_t< int >& e) {
		ran_sieve* cl = (ran_sieve *)_c;
		cl->multi_access_age(n, a, b, c, d, e);
	});
	m.def("ran_sieve_queue_stats", [](void* _c, py::array_t< int >& n, py::array_t< double >& sum, py::array_t< double >& sum2) {
		ran_sieve* c = (ran_sieve *)_c;
		c->queue_stats(n, sum, sum2);
	});
	m.def("ran_sieve_hitrate", [](void* _c) {
		ran_sieve* c = (ran_sieve *)_c;
		return c->hit_rate();
	});
	m.def("ran_sieve_data", [](void* _c) -> py::tuple {
		ran_sieve* cl = (ran_sieve *)_c;
		int _access, _miss, _cachefill, _recycle, _examined, _sum_counter;
		cl->data(_access, _miss, _cachefill, _recycle, _examined, _sum_counter);
		return py::make_tuple(_access, _miss, _cachefill, _recycle, _examined, _sum_counter);
	});
}
