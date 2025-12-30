#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class lfu
{
	int C = 0;

	struct entry
	{
		int32_t addr = -1;
		int freq = 0;
		int last = 0;
	};

	std::vector<entry> slots;  // physical cache slots
	std::vector<int> loc;	   // addr -> slot index or -1

	int len = 0;
	int n_access = 0;
	int n_miss = 0;
	int n_cachefill = 0;

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

	int victim_index() const
	{
		// Choose the item with the smallest frequency; break ties by oldest last-use time.
		int victim = 0;
		int best_freq = slots[0].freq;
		int best_last = slots[0].last;
		for (int i = 1; i < len; i++)
		{
			int f = slots[i].freq;
			int l = slots[i].last;
			if (f < best_freq || (f == best_freq && l < best_last))
			{
				victim = i;
				best_freq = f;
				best_last = l;
			}
		}
		return victim;
	}

public:
	lfu(int _C) : C(_C)
	{
		if (C <= 0)
			throw std::invalid_argument("Cache size must be positive");
		slots.assign(C, entry{});
		loc.assign(100000, -1);
	}

	void access(int32_t addr)
	{
		n_access++;
		if (len < C)
			n_cachefill = n_access;

		expand(addr);
		int pos = loc[addr];
		if (pos == -1)
		{
			n_miss++;
			if (len < C)
			{
				slots[len] = entry{addr, 1, n_access};
				loc[addr] = len;
				len++;
				return;
			}

			int victim = victim_index();
			loc[slots[victim].addr] = -1;
			slots[victim] = entry{addr, 1, n_access};
			loc[addr] = victim;
			return;
		}

		auto& e = slots[pos];
		e.freq++;
		e.last = n_access;
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
		for (int i = 0; i < len; i++)
		{
			if (slots[i].addr != -1)
				out_ptr[n++] = slots[i].addr;
		}
		return n;
	}

	double hit_rate() const
	{
		if (n_access <= n_cachefill)
			return 1.0 - (n_miss * 1.0 / std::max(1, n_access));
		double miss_rate = (n_miss - C) * 1.0 / std::max(1, (n_access - n_cachefill));
		return 1.0 - miss_rate;
	}

	void data(int& _access, int& _miss, int& _cachefill) const
	{
		_access = n_access;
		_miss = n_miss;
		_cachefill = n_cachefill;
	}
};

PYBIND11_MODULE(_lfu, m)
{
	py::class_<lfu>(m, "lfu")
		.def(py::init<int>())
		.def("multi_access", &lfu::multi_access)
		.def("contents", &lfu::contents)
		.def("hit_rate", &lfu::hit_rate)
		.def("data", &lfu::data);

	m.def("lfu_create", [](int C) {
		return new lfu(C);
	});

	m.def("lfu_run", [](void* _l, int n, py::array_t<int32_t>& a) {
		lfu* l = (lfu*)_l;
		l->multi_access(n, a);
	});

	m.def("lfu_contents", [](void* _l, py::array_t<int32_t>& out) {
		lfu* l = (lfu*)_l;
		return l->contents(out);
	});

	m.def("lfu_hitrate", [](void* _l) {
		lfu* l = (lfu*)_l;
		return l->hit_rate();
	});

	m.def("lfu_data", [](py::object _l) -> py::tuple {
		if (py::isinstance<lfu>(_l))
		{
			lfu l = _l.cast<lfu>();
			int _access, _miss, _cachefill;
			l.data(_access, _miss, _cachefill);
			return py::make_tuple(_access, _miss, _cachefill);
		}
		throw std::invalid_argument("Not passing lfu object");
	});
}
