#include <stdint.h>
#include <unordered_map>
#include <vector>
#include <queue>
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class belady_min
{
	int C = 0;
	int n_access = 0;
	int n_miss = 0;
	int n_cachefill = 0;
	std::vector<int> contents_vec;

public:
	belady_min(int _C) : C(_C) {}
	~belady_min() {}

	void multi_access(int n, py::array_t<int32_t> &addrs)
	{
		n_access = n_miss = n_cachefill = 0;
		contents_vec.clear();
		if (n <= 0 || C < 0)
			return;

		const int32_t *a = addrs.data();
		const int INF = n + 1;

		// Precompute next occurrence for each position
		std::vector<int> next_idx(n, INF);
		std::unordered_map<int, int> last_pos;
		last_pos.reserve(n * 2);
		for (int i = n - 1; i >= 0; --i)
		{
			int addr = a[i];
			auto it = last_pos.find(addr);
			next_idx[i] = (it == last_pos.end()) ? INF : it->second;
			last_pos[addr] = i;
		}

		std::unordered_map<int, int> cache_next;
		cache_next.reserve(C * 2 + 1);
		std::priority_queue<std::pair<int, int>> pq; // (next_idx, addr) max-heap by next_idx
		int distinct_seen = 0;

		auto update_fill = [&](int size_now) {
			if (n_cachefill == 0)
			{
				int target = std::min(C, distinct_seen);
				if (size_now >= target && target > 0)
					n_cachefill = n_access;
			}
		};

		for (int i = 0; i < n; ++i)
		{
			int addr = a[i];
			int nxt = next_idx[i];
			n_access++;

			auto it = cache_next.find(addr);
			if (it != cache_next.end())
			{
				it->second = nxt;
				pq.push({nxt, addr});
				continue;
			}

			distinct_seen++;
			n_miss++;

			if (C > 0 && static_cast<int>(cache_next.size()) >= C)
			{
				while (!pq.empty())
				{
					auto top = pq.top();
					auto ct = cache_next.find(top.second);
					if (ct != cache_next.end() && ct->second == top.first)
					{
						cache_next.erase(ct);
						pq.pop();
						break;
					}
					pq.pop();
				}
			}

			if (C > 0)
			{
				cache_next[addr] = nxt;
				pq.push({nxt, addr});
				update_fill(static_cast<int>(cache_next.size()));
			}
		}

		if (n_cachefill == 0)
			n_cachefill = n_access; // never filled to capacity or distinct set, treat run as warmup

		contents_vec.reserve(cache_next.size());
		for (const auto &kv : cache_next)
			contents_vec.push_back(kv.first);
	}

	int contents(py::array_t<int32_t> &out)
	{
		int32_t *out_ptr = out.mutable_data();
		int n = 0;
		for (int addr : contents_vec)
			out_ptr[n++] = addr;
		return n;
	}

	double hit_rate(void)
	{
		if (n_access == 0)
			return 0.0;
		int warm = n_access - n_cachefill;
		if (warm <= 0)
			return 1.0 - (static_cast<double>(n_miss) / n_access);
		double miss_rate = (n_miss - C) * 1.0 / warm;
		return 1 - miss_rate;
	}

	void data(int &_access, int &_miss, int &_cachefill)
	{
		_access = n_access;
		_miss = n_miss;
		_cachefill = n_cachefill;
	}
};

PYBIND11_MODULE(_min, m)
{
	py::class_<belady_min>(m, "belady_min")
		.def(py::init<int>(), py::arg("C"))
		.def("multi_access", &belady_min::multi_access, py::arg("n"), py::arg("addrs"))
		.def("contents", &belady_min::contents)
		.def("hit_rate", &belady_min::hit_rate)
		.def("data", &belady_min::data);

	m.def("min_create", [](int C) {
		return new belady_min(C);
	});
	m.def("min_run", [](void *_c, int n, py::array_t<int32_t> &a) {
		belady_min *c = (belady_min *)_c;
		c->multi_access(n, a);
	});
	m.def("min_contents", [](void *_c, py::array_t<int32_t> &out) {
		belady_min *c = (belady_min *)_c;
		return c->contents(out);
	});
	m.def("min_hitrate", [](void *_c) {
		belady_min *c = (belady_min *)_c;
		return c->hit_rate();
	});
	m.def("min_data", [](void *_c) -> py::tuple {
		belady_min *c = (belady_min *)_c;
		int _access, _miss, _cachefill;
		c->data(_access, _miss, _cachefill);
		return py::make_tuple(_access, _miss, _cachefill);
	});
}
