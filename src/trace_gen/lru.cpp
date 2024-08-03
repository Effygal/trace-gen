#include <map>
#include <unordered_map>
#include <assert.h>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

/*
  +-+-+-+-+-+-+-+-+-+-+-+-+-+
  | | |x| |x| |x| | | | | | |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+
   0   ^         ^
	   |         head ->
	   tail ->
  head points to first unoccupied entry
  tail may point to empty entry
 */

class LRU {
 
	int M = 0;
	int C = 0;
	std::vector<int> map; // track item position in cache
	int tail = 0, head = 0;
	std::vector<int> cache;

	std::vector<int> ref;	// time of most recent ref
	std::vector<int> enter; // time entered cache

	int n_evict = 0;
	double s_evict_ref = 0;
	double s2_evict_ref = 0;

	int len = 0;

	int n_cachefill = 0;
	int n_access = 0;
	int n_miss = 0;

public:
	LRU(int _C)
	{
		C = _C;
		map.resize(100000, -1);
		enter.resize(100000, -1);
		ref.resize(100000, -1);
		cache.resize(2 * _C, -1);
	}
	~LRU() {}

	// invalid entries in cache, map are flagged with -1
	// need specific flag if we want to use uint...

	void verify(void)
	{
		for (int i = tail; i < head; i++)
			assert(cache[i] == -1 || map[cache[i]] == i); //assert invalid cache entry or item has been record correctly in map
		for (unsigned int i = 0; i < map.size(); i++)
		{
			assert(map[i] == -1 || cache[map[i]] == i); //assert invalid map entry or item in map and has correct record of index in cache 
			assert(map[i] < head);
		}
	}

	int contents(py::array_t< int32_t >& out)
	{
		int32_t* out_ptr = out.mutable_data();
		int i, n;
		for (i = head - 1, n = 0; i >= 0; i--)
			if (cache[i] != -1)
				out_ptr[n++] = cache[i];
		return n;
	}

	void pull(int addr) //erase item record
	{
		assert(map[addr] != -1);
		cache[map[addr]] = -1;
		map[addr] = -1;
		len--;
	}

	int pop(void) //remove item from tail
	{
		while (cache[tail] == -1)
			tail++;
		int addr = cache[tail];
		pull(addr);
		return addr;
	}

	void push(int addr)
	{
		if (head >= 2 * C) 
		{
			int i, j;
			for (i = 0, j = 0; i < head; i++)
				if (cache[i] != -1)
				{
					map[cache[i]] = j;
					cache[j++] = cache[i];
				}
			tail = 0;
			head = j;
		}
		map[addr] = head; //insert item from head, track index
		cache[head++] = addr;
		len++;
	}

	void access(unsigned int addr)
	{
		n_access++;
		if (len < C)
			n_cachefill = n_access;
		if (addr >= map.size())
			map.resize(addr * 3 / 2, -1);
		if (map[addr] == -1)
			n_miss++;
		else
			pull(addr); //hit erase
		push(addr);
		if (len > C)
			pop();
	}

	void access_verbose(unsigned int addr, int32_t* miss, int32_t* evictee,
						int32_t* last_ref, int32_t* entered)
	{
		n_access++;
		if (len < C)
			n_cachefill = n_access;
		if (addr >= map.size())
		{
			int n = addr * 3 / 2;
			map.resize(n, -1);
			ref.resize(n, 0);
			enter.resize(n, 0);
		}
		if (map[addr] == -1)
		{
			n_miss++;
			enter[addr] = n_access;
			ref[addr] = n_access;
		}
		else
		{
			ref[addr] = n_access;
			pull(addr);
		}
		push(addr);
		if (len > C)
		{
			int e = pop();
			*miss= 1;
			*evictee = e;
			*last_ref = n_access - ref[e];
			*entered = n_access - enter[e];

			n_evict++;
			s_evict_ref += *last_ref;
			s2_evict_ref += 1.0 * (*last_ref) * (*last_ref);
		}
	}

	void queue_stats(py::array_t< int32_t >& n, py::array_t<double>& s, py::array_t<double>& s2)
	{
		int32_t* n_ptr = n.mutable_data();
		double* s_ptr = s.mutable_data();
		double* s2_ptr = s2.mutable_data();

		*n_ptr = n_evict;
		*s_ptr = s_evict_ref;
		*s2_ptr = s2_evict_ref;
	}

	void multi_access(int n, py::array_t<int>& addrs)
	{
		int32_t* addrs_ptr = addrs.mutable_data();

		for (int i = 0; i < n; i++)
		{
			access(addrs_ptr[i]);
		}
	}

	void multi_access_age(int n, py::array_t<int>& addrs, py::array_t< int32_t >& misses,
						  py::array_t< int32_t >& evicted, py::array_t< int32_t >& age1, py::array_t< int32_t >& age2)
	{
		int32_t* addrs_ptr = addrs.mutable_data();
		int32_t* misses_ptr = misses.mutable_data();
		int32_t* evicted_ptr = evicted.mutable_data();
		int32_t* age1_ptr = age1.mutable_data();
		int32_t* age2_ptr = age2.mutable_data();

		for (int i = 0; i < n; i++)
			access_verbose(addrs_ptr[i], &misses_ptr[i], &evicted_ptr[i], &age1_ptr[i], &age2_ptr[i]);
	}

	double hit_rate(void)
	{
		double miss_rate = (n_miss - C) * 1.0 / (n_access - n_cachefill);
		return 1 - miss_rate;
	}

	void data(int& _access, int& _miss, int& _cachefill)
	{
		_access = n_access;
		_miss = n_miss;
		_cachefill = n_cachefill;
	}
};

PYBIND11_MODULE(_lru, m) {
    py::class_<LRU>(m, "LRU")
		.def(py::init<int>())
		.def("multi_access", &LRU::multi_access)
		.def("contents", &LRU::contents)
		.def("multi_access_age", &LRU::multi_access_age)
		.def("hit_rate", &LRU::hit_rate)
		.def("queue_stats", &LRU::queue_stats)
		.def("data", &LRU::data);

	m.def("lru_create", [](int C) {
		return new LRU(C); 
		});
	m.def("lru_run", [](void* _l, int n, py::array_t< int32_t >& a) {
		LRU* l = (LRU *)_l;
		l->multi_access(n, a); 
		});
	m.def("lru_contents", [](void* _l, py::array_t< int32_t >& out) {
		LRU* l = (LRU *)_l;
		return l->contents(out); 
		});
	m.def("lru_run_age", [](void* _l, int n, py::array_t< int32_t >& a, py::array_t< int32_t >& b, py::array_t< int32_t >& c, py::array_t< int32_t >& d, py::array_t< int32_t >& e) {
		LRU* l = (LRU *)_l;
		l->multi_access_age(n, a, b, c, d, e); 
		});
	m.def("lru_hitrate", [](void* _l) {
		LRU* l = (LRU *)_l;
		return l->hit_rate(); 
		});
	m.def("lru_queue_stats", [](void* _l, py::array_t< int32_t >& n, py::array_t<double>& s, py::array_t<double>& s2) {
		LRU* l = (LRU *)_l;
		l->queue_stats(n, s, s2); 
		});

	m.def("lru_data", [](py::object _l) -> py::tuple {
		if (py::isinstance< LRU >(_l)) {
			LRU l = _l.cast< LRU >();
			int _access, _miss, _cachefill;
			l.data(_access, _miss, _cachefill);
			return py::make_tuple(_access, _miss, _cachefill);
		} else { 
			throw std::invalid_argument("Not passing LRU object");
		}
	});
}
