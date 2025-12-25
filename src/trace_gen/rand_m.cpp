#include <assert.h>
#include <stdint.h>
#include <algorithm>
#include <random>
#include <stdexcept>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class rand_m
{
	std::vector<int> list_sizes;
	std::vector<int> offsets;
	std::vector<int> heads;

	int total_m = 0;
	std::vector<int32_t> cells; // physical slots, -1 means empty
	std::vector<int> loc;		// addr -> physical slot index in `cells` (or -1)

	int len = 0;
	int n_access = 0;
	int n_miss = 0;
	int fill_access = 0;
	int fill_miss = 0;

	static std::mt19937_64& rng()
	{
		static std::mt19937_64 rng(std::random_device{}());
		return rng;
	}

	void expand(int32_t addr)
	{
		if (addr < 0)
			throw std::invalid_argument("Address must be non-negative");
		if (addr >= (int32_t)loc.size())
		{
			int n = addr * 3 / 2 + 1;
			loc.resize(n, -1);
		}
	}

	int list_of_slot(int slot) const
	{
		auto it = std::upper_bound(offsets.begin(), offsets.end(), slot);
		return std::max(0, (int)(it - offsets.begin()) - 1);
	}

	int list_pos_of_slot(int list, int slot) const
	{
		return slot - offsets[list];
	}

	int logical_pos(int list, int phys_pos) const
	{
		int m = list_sizes[list];
		return (phys_pos - heads[list] + m) % m;
	}

	int phys_slot(int list, int logical_pos0) const
	{
		int m = list_sizes[list];
		int phys_pos = (heads[list] + logical_pos0) % m;
		return offsets[list] + phys_pos;
	}

	int rand_pos(int list)
	{
		std::uniform_int_distribution<int> dist(0, list_sizes[list] - 1);
		return dist(rng());
	}

public:
	rand_m(std::vector<int> m)
		: list_sizes(std::move(m))
	{
		if (list_sizes.empty())
			throw std::invalid_argument("m must have at least one list size");
		for (int mi : list_sizes)
		{
			if (mi <= 0)
				throw std::invalid_argument("All list sizes must be >= 1");
		}

		offsets.resize(list_sizes.size() + 1, 0);
		for (size_t i = 0; i < list_sizes.size(); i++)
			offsets[i + 1] = offsets[i] + list_sizes[i];
		total_m = offsets.back();

		heads.assign(list_sizes.size(), 0);
		cells.assign(total_m, -1);
		loc.assign(100000, -1);
	}

	void access(int32_t addr)
	{
		n_access++;
		if (len < total_m)
			fill_access = n_access;

		expand(addr);
		int slot = loc[addr];
		if (slot == -1)
		{
			n_miss++;
			if (len < total_m)
				fill_miss = n_miss;

			int rp = rand_pos(0);
			int target = phys_slot(0, rp);
			int32_t evicted = cells[target];
			if (evicted != -1)
			{
				loc[evicted] = -1;
				len--;
			}
			cells[target] = addr;
			loc[addr] = target;
			if (evicted == -1)
				len++;
			return;
		}

		int list = list_of_slot(slot);
		if (list == (int)list_sizes.size() - 1)
			return;

		int rp = rand_pos(list + 1);
		int target = phys_slot(list + 1, rp);
		int32_t displaced = cells[target];

		cells[target] = addr;
		loc[addr] = target;

		cells[slot] = displaced;
		if (displaced != -1)
			loc[displaced] = slot;
	}

	void multi_access(int n, py::array_t<int32_t>& addrs)
	{
		int32_t* addrs_ptr = addrs.mutable_data();
		for (int i = 0; i < n; i++)
			access(addrs_ptr[i]);
	}

	int contents(py::array_t<int32_t>& out)
	{
		int32_t* out_ptr = out.mutable_data();
		int n = 0;
		for (size_t li = 0; li < list_sizes.size(); li++)
		{
			for (int p = 0; p < list_sizes[li]; p++)
			{
				int slot = phys_slot((int)li, p);
				int32_t v = cells[slot];
				if (v != -1)
					out_ptr[n++] = v;
			}
		}
		return n;
	}

	double hit_rate() const
	{
		if (n_access <= fill_access)
			return 1.0 - (n_miss * 1.0 / std::max(1, n_access));
		double miss_rate = (n_miss - fill_miss) * 1.0 / (n_access - fill_access);
		return 1.0 - miss_rate;
	}

	void data(int& _access, int& _miss, int& _fill_access, int& _fill_miss) const
	{
		_access = n_access;
		_miss = n_miss;
		_fill_access = fill_access;
		_fill_miss = fill_miss;
	}

	int cache_size() const { return total_m; }
};

PYBIND11_MODULE(_rand_m, m)
{
	py::class_<rand_m>(m, "rand_m")
		.def(py::init<std::vector<int>>(),
			 py::arg("m"))
		.def("multi_access", &rand_m::multi_access)
		.def("contents", &rand_m::contents)
		.def("hit_rate", &rand_m::hit_rate)
		.def("cache_size", &rand_m::cache_size);

	m.def("rand_m_create", [](std::vector<int> m) {
		return new rand_m(std::move(m));
	},
		  py::arg("m"));

	m.def("rand_m_run", [](void* _r, int n, py::array_t<int32_t>& a) {
		rand_m* r = (rand_m*)_r;
		r->multi_access(n, a);
	});

	m.def("rand_m_contents", [](void* _r, py::array_t<int32_t>& out) {
		rand_m* r = (rand_m*)_r;
		return r->contents(out);
	});

	m.def("rand_m_hitrate", [](void* _r) {
		rand_m* r = (rand_m*)_r;
		return r->hit_rate();
	});

	m.def("rand_m_data", [](py::object _r) -> py::tuple {
		if (py::isinstance<rand_m>(_r))
		{
			rand_m r = _r.cast<rand_m>();
			int a, m, fa, fm;
			r.data(a, m, fa, fm);
			return py::make_tuple(a, m, fa, fm);
		}
		throw std::invalid_argument("Not passing rand_m object");
	});
}
