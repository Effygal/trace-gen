#include <stdio.h>
#include <vector>
#include <set>
#include <unordered_set>
#include <assert.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class fifo
{
	int C = 0;
	std::vector<int> cache;
	std::vector<int> enter;

	int n_evict = 0;
	double s_evict = 0;
	double s2_evict = 0;

	std::vector<char> map;

	int in = 0, out = 0;
	int n_cachefill = 0;
	int n_access = 0;
	int n_miss = 0;

public:
	fifo(int _C)
	{
		C = _C;
		cache.resize(C + 1);
		enter.resize(C + 1, 0);
		map.resize(100000, 0);
	}
	~fifo() {}

	void access(int32_t addr)
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

	int contents(py::array_t<int>& val)
	{
		int *val_ptr = val.mutable_data();
		int i, n = 0;
		for (i = (in + C) % (C + 1);; i = (i + C) % (C + 1))
		{
			val_ptr[n++] = cache[i];
			if (i == out)
				break;
		}
		return n;
	}

	void multi_access(int n, py::array_t< int32_t >& addrs)
	{
		int32_t *addrs_ptr = addrs.mutable_data();
		
		for (int i = 0; i < n; i++)
			access(addrs_ptr[i]);
	}

	void multi_access_verbose(int n, py::array_t<int32_t>& addrs, py::array_t< int >& misses)
	{
		int32_t *addrs_ptr = addrs.mutable_data();
		int *misses_ptr = misses.mutable_data();

		for (int i = 0; i < n; i++)
		{

			int nm = n_miss;
			access(addrs_ptr[i]);
			if (n_miss != nm)
				misses_ptr[i] = 1;
		}
	}

	void multi_access_age(int n, py::array_t<int32_t>& addrs, py::array_t< int >& misses, py::array_t<int>& age)
	{
		int32_t *addrs_ptr = addrs.mutable_data();
		int *misses_ptr = misses.mutable_data();
		int *age_ptr = age.mutable_data();

		std::vector<int> times;
		times.resize(C, 0);
		int t = 1;
		for (int i = 0; i < n; i++, t++)
		{
			n_access++;
			auto addr = addrs_ptr[i];
			if (addr >= map.size())
				map.resize(addr * 3 / 2, 0);
			if (!map[addr])
			{
				n_miss++;
				misses_ptr[i] = 1;
				if ((in + 1) % (C + 1) != out)
				{ // cache not full
					n_cachefill = n_access;
				}
				else
				{
					int evictee = cache[out];
					age_ptr[i] = t - times[out];
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

	void queue_stats(py::array_t< int32_t >& n, py::array_t<double>& s, py::array_t<double>& s2)
	{
		int32_t* n_ptr = n.mutable_data();
		double* s_ptr = s.mutable_data();
		double* s2_ptr = s2.mutable_data();

		*n_ptr = n_evict;
		*s_ptr = s_evict;
		*s2_ptr = s2_evict;
	}

	void data(int &_access, int &_miss, int &_cachefill)
	{
		_access = n_access;
		_miss = n_miss;
		_cachefill = n_cachefill;
	}
};

PYBIND11_MODULE(_fifo, m)
{
	py::class_<fifo>(m, "fifo")
		.def(py::init<int>())
		.def("multi_access", &fifo::multi_access)
		.def("contents", &fifo::contents)
		.def("multi_access_verbose", &fifo::multi_access_verbose)
		.def("multi_access_age", &fifo::multi_access_age)
		.def("hit_rate", &fifo::hit_rate)
		.def("queue_stats", &fifo::queue_stats)
		.def("data", &fifo::data);
	m.def("fifo_create", [](int C) {
		return new fifo(C);
	});
	m.def("fifo_run", [](void *_f, int n, py::array_t< int32_t >& a) {
		fifo *f = (fifo *)_f;
		f->multi_access(n, a);
	});
	m.def("fifo_contents", [](void *_f, py::array_t< int >& out) {
		fifo *f = (fifo *)_f;
		f->contents(out);
	});
	m.def("fifo_run_verbose", [](void *_f, int n, py::array_t< int32_t >& a, py::array_t< int >& b) {
		fifo *f = (fifo *)_f;
		f->multi_access_verbose(n, a, b);
	});
	m.def("fifo_run_age", [](void *_f, int n, py::array_t< int32_t >& a, py::array_t< int >& b, py::array_t< int >& c) {
		fifo *f = (fifo *)_f;
		f->multi_access_age(n, a, b, c);
	});
	m.def("fifo_hitrate", [](void *_f) {
		fifo *f = (fifo *)_f;
		return f->hit_rate();
	});
	m.def("fifo_queue_stats", [](void *_f, py::array_t< int32_t >& n, py::array_t<double>& s, py::array_t<double>& s2) {
		fifo *f = (fifo *)_f;
		f->queue_stats(n, s, s2);
	});
	m.def("fifo_data", [](py::object _f) -> py::tuple {
		if (py::isinstance<fifo>(_f))
		{
			fifo f = _f.cast<fifo>();
			int _access, _miss, _cachefill;
			f.data(_access, _miss, _cachefill);
			return py::make_tuple(_access, _miss, _cachefill);
		}
		else
		{
			throw std::invalid_argument("Not passing fifo object");
		}
	});
}
