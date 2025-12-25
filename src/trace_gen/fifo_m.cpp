#include <assert.h>
#include <stdint.h>
#include <algorithm>
#include <stdexcept>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class fifo_m
{
	std::vector<int> list_sizes;
	std::vector<int> offsets;
	std::vector<int> heads;

	int total_m = 0;
	std::vector<int32_t> cells; // physical slots, -1 means empty
	std::vector<int> loc;		// addr -> physical slot index in `cells` (or -1)

	bool strict_mode = false;
	bool lru_mode = false;

	int len = 0;
	int n_access = 0;
	int n_miss = 0;
	int fill_access = 0;
	int fill_miss = 0;

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

	// Insert `addr` in logical position 0 (position 1 in the paper) of `list`,
	// shifting all items back by one position. Returns the displaced item that
	// was in the last position (or -1). Does not change `len`.
	int32_t insert_front_shift_displace(int list, int32_t addr)
	{
		int m = list_sizes[list];
		int new_head = (heads[list] - 1 + m) % m;
		int new_head_slot = offsets[list] + new_head;

		int32_t displaced = cells[new_head_slot];
		if (displaced != -1)
			loc[displaced] = -1;

		cells[new_head_slot] = addr;
		loc[addr] = new_head_slot;

		heads[list] = new_head;
		return displaced;
	}

	// Same as insert_front_shift_displace, but evicts the displaced item from the cache,
	// updating `len` and `loc`.
	void insert_front_shift_evict(int list, int32_t addr)
	{
		int32_t displaced = insert_front_shift_displace(list, addr);
		if (displaced == -1)
			len++; // filled a previously-empty slot
	}

	void strict_promote(int list, int logical_pos0, int32_t addr)
	{
		int32_t displaced = insert_front_shift_displace(list + 1, addr);

		for (int t = logical_pos0; t >= 1; t--)
		{
			int dst = phys_slot(list, t);
			int src = phys_slot(list, t - 1);
			cells[dst] = cells[src];
			if (cells[dst] != -1)
				loc[cells[dst]] = dst;
		}
		int head_slot = phys_slot(list, 0);
		cells[head_slot] = displaced;
		if (displaced != -1)
			loc[displaced] = head_slot;
	}

	void lru_move_to_front_last_list(int logical_pos0, int32_t addr)
	{
		int list = (int)list_sizes.size() - 1;
		for (int t = logical_pos0; t >= 1; t--)
		{
			int dst = phys_slot(list, t);
			int src = phys_slot(list, t - 1);
			cells[dst] = cells[src];
			if (cells[dst] != -1)
				loc[cells[dst]] = dst;
		}
		int head_slot = phys_slot(list, 0);
		cells[head_slot] = addr;
		loc[addr] = head_slot;
	}

public:
	fifo_m(std::vector<int> m, bool strict, bool lru)
		: list_sizes(std::move(m)), strict_mode(strict || lru), lru_mode(lru)
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
			insert_front_shift_evict(0, addr);
			return;
		}

		int list = list_of_slot(slot);
		int phys_pos = list_pos_of_slot(list, slot);
		int pos0 = logical_pos(list, phys_pos);

		if (list == (int)list_sizes.size() - 1)
		{
			if (lru_mode && pos0 > 0)
				lru_move_to_front_last_list(pos0, addr);
			return;
		}

		if (!strict_mode)
		{
			int old_slot = slot;
			int32_t displaced = insert_front_shift_displace(list + 1, addr);
			cells[old_slot] = displaced;
			if (displaced != -1)
				loc[displaced] = old_slot;
			return;
		}

		strict_promote(list, pos0, addr);
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

PYBIND11_MODULE(_fifo_m, m)
{
	py::class_<fifo_m>(m, "fifo_m")
		.def(py::init<std::vector<int>, bool, bool>(),
			 py::arg("m"),
			 py::arg("strict") = false,
			 py::arg("lru") = false)
		.def("multi_access", &fifo_m::multi_access)
		.def("contents", &fifo_m::contents)
		.def("hit_rate", &fifo_m::hit_rate)
		.def("cache_size", &fifo_m::cache_size);

	m.def("fifo_m_create", [](std::vector<int> m, bool strict, bool lru) {
		return new fifo_m(std::move(m), strict, lru);
	},
		  py::arg("m"),
		  py::arg("strict") = false,
		  py::arg("lru") = false);

	m.def("fifo_m_run", [](void* _f, int n, py::array_t<int32_t>& a) {
		fifo_m* f = (fifo_m*)_f;
		f->multi_access(n, a);
	});

	m.def("fifo_m_contents", [](void* _f, py::array_t<int32_t>& out) {
		fifo_m* f = (fifo_m*)_f;
		return f->contents(out);
	});

	m.def("fifo_m_hitrate", [](void* _f) {
		fifo_m* f = (fifo_m*)_f;
		return f->hit_rate();
	});

	m.def("fifo_m_data", [](py::object _f) -> py::tuple {
		if (py::isinstance<fifo_m>(_f))
		{
			fifo_m f = _f.cast<fifo_m>();
			int a, m, fa, fm;
			f.data(a, m, fa, fm);
			return py::make_tuple(a, m, fa, fm);
		}
		throw std::invalid_argument("Not passing fifo_m object");
	});
}
