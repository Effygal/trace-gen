#include <algorithm>
#include <list>
#include <stdint.h>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class sieve
{
	int C = 0;
	std::list<int> cache; // front = head (newest), back = tail (oldest)
	std::vector<char> map;		  
	std::vector<int> abit;	   
	std::vector<int> enter_time;   
	std::vector<int> ref_time;	   
	int n_top = 0;
	double sum_top = 0, sum_top2 = 0;

	int n_cachefill = 0;
	int n_access = 0;
	int n_miss = 0;
	int n_recycle = 0;
	int n_examined = 0;
	int sum_abit = 0;

	std::list<int>::iterator hand;
	bool hand_valid = false;

	void expand(int32_t addr)
	{
		if (addr >= static_cast<int32_t>(map.size()))
		{
			int n = addr * 3 / 2 + 1;
			map.resize(n, 0);
			abit.resize(n, 0);
			enter_time.resize(n, 0);
			ref_time.resize(n, 0);
		}
	}

	int pop(int* ref_age = nullptr, int* ent_age = nullptr)
	{
		if (cache.empty())
			return -1;

		if (!hand_valid)
		{
			hand = cache.end();
			hand_valid = true;
		}
		if (hand == cache.end())
			hand = std::prev(cache.end()); 
		auto it = hand;
		while (true)
		{
			int addr = *it;
			n_examined++;
			if (abit[addr])
			{
				sum_abit += abit[addr];
				abit[addr] = 0;
				n_recycle++;

				if (it == cache.begin())
					it = std::prev(cache.end());
				else
					--it;
				continue;
			}

			int r_age = n_access - ref_time[addr];
			int e_age = n_access - enter_time[addr];
			int age = e_age;
			sum_top += age;
			sum_top2 += (age * age);
			n_top++;

			if (it == cache.begin())
				hand_valid = false;
			else
			{
				hand = std::prev(it);
				hand_valid = true;
			}

			cache.erase(it);
			map[addr] = 0;
			abit[addr] = 0;

			if (ref_age)
				*ref_age = r_age;
			if (ent_age)
				*ent_age = e_age;
			return addr;
		}
	}

	void push(int addr)
	{
		cache.push_front(addr);
		map[addr] = 1;
		abit[addr] = 0;
		enter_time[addr] = ref_time[addr] = n_access;
	}

public:
	sieve(int _C) : C(_C)
	{
		map.resize(100000, 0);
		abit.resize(100000, 0);
		enter_time.resize(100000, 0);
		ref_time.resize(100000, 0);
	}
	~sieve() {}

	bool full(void)
	{
		return static_cast<int>(cache.size()) >= C;
	}

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
			abit[addr] += 1;
			ref_time[addr] = n_access;
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
			abit[addr] += 1;
			ref_time[addr] = n_access;
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

PYBIND11_MODULE(_sieve, m)
{
	py::class_<sieve>(m, "sieve")
		.def(py::init<int>())
		.def("multi_access", &sieve::multi_access)
		.def("contents", &sieve::contents)
		.def("multi_access_age", &sieve::multi_access_age)
		.def("queue_stats", &sieve::queue_stats)
		.def("hit_rate", &sieve::hit_rate)
		.def("data", &sieve::data);
	m.def("sieve_create", [](int C) {
		return new sieve(C);
	});
	m.def("sieve_run", [](void* _c, int n, py::array_t< int32_t >& a) {
		sieve* c = (sieve *)_c;
		c->multi_access(n, a);
	});
	m.def("sieve_contents", [](void* _c, py::array_t< int >& out) {
		sieve* c = (sieve *)_c;
		return c->contents(out);
	});
	m.def("sieve_run_age", [](void* _c, int n, py::array_t< int32_t >& a, py::array_t< int >& b, py::array_t< int >& c, py::array_t< int >& d, py::array_t< int >& e) {
		sieve* cl = (sieve *)_c;
		cl->multi_access_age(n, a, b, c, d, e);
	});
	m.def("sieve_queue_stats", [](void* _c, py::array_t< int >& n, py::array_t< double >& sum, py::array_t< double >& sum2) {
		sieve* c = (sieve *)_c;
		c->queue_stats(n, sum, sum2);
	});
	m.def("sieve_hitrate", [](void* _c) {
		sieve* c = (sieve *)_c;
		return c->hit_rate();
	});
	m.def("sieve_data", [](void* _c) -> py::tuple {
		sieve* cl = (sieve *)_c;
		int _access, _miss, _cachefill, _recycle, _examined, _sum_abit;
		cl->data(_access, _miss, _cachefill, _recycle, _examined, _sum_abit);
		return py::make_tuple(_access, _miss, _cachefill, _recycle, _examined, _sum_abit);
	});
}
