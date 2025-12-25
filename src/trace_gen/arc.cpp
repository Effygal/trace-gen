#include <map>
#include <unordered_map>
#include <assert.h>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

class arc {
    int C = 0;
    int M = 0;
    std::unordered_map<int, int> t1, t2, b1, b2;
    std::vector<int> t1_list, t2_list, b1_list, b2_list;
    int p;
    int hits, misses;

    void replace(int addr) {
        if (!t1.empty() && (t1.find(addr) == t1.end() || t1.size() > p)) {
            int old = t1_list.back();
            t1_list.pop_back();
            t1.erase(old);
            b1_list.insert(b1_list.begin(), old);
            b1[old] = 0;
        } else {
            int old = t2_list.back();
            t2_list.pop_back();
            t2.erase(old);
            b2_list.insert(b2_list.begin(), old);
            b2[old] = 0;
        }
    }

public:
    arc(int _C) : C(_C), p(0), hits(0), misses(0) {}

    void access(int addr) {
        if (t1.find(addr) != t1.end()) {
            hits++;
            t1_list.erase(std::remove(t1_list.begin(), t1_list.end(), addr), t1_list.end());
            t2_list.insert(t2_list.begin(), addr);
            t2[addr] = 0;
        } else if (t2.find(addr) != t2.end()) {
            hits++;
            t2_list.erase(std::remove(t2_list.begin(), t2_list.end(), addr), t2_list.end());
            t2_list.insert(t2_list.begin(), addr);
            t2[addr] = 0;
        } else {
            misses++;
            if (b1.find(addr) != b1.end()) {
                p = std::min(C, p + std::max(int(b2.size() / b1.size()), 1));
                replace(addr);
                b1_list.erase(std::remove(b1_list.begin(), b1_list.end(), addr), b1_list.end());
                b1.erase(addr);
                t2_list.insert(t2_list.begin(), addr);
                t2[addr] = 0;
            } else if (b2.find(addr) != b2.end()) {
                p = std::max(0, p - std::max(int(b1.size() / b2.size()), 1));
                replace(addr);
                b2_list.erase(std::remove(b2_list.begin(), b2_list.end(), addr), b2_list.end());
                b2.erase(addr);
                t2_list.insert(t2_list.begin(), addr);
                t2[addr] = 0;
            } else {
                if (t1.size() + b1.size() == C) {
                    if (t1.size() < C) {
                        b1_list.pop_back();
                        b1.erase(b1_list.back());
                        replace(addr);
                    } else {
                        t1_list.pop_back();
                        t1.erase(t1_list.back());
                    }
                } else if (t1.size() + t2.size() + b1.size() + b2.size() >= C) {
                    if (t1.size() + t2.size() + b1.size() + b2.size() == 2 * C) {
                        b2_list.pop_back();
                        b2.erase(b2_list.back());
                    }
                    replace(addr);
                }
                t1_list.insert(t1_list.begin(), addr);
                t1[addr] = 0;
            }
        }
    }

    void access_verbose(int addr, int32_t* miss, int32_t* evictee, int32_t* last_ref, int32_t* entered) {
        *miss = (t1.find(addr) == t1.end() && t2.find(addr) == t2.end());
        *evictee = -1;
        *last_ref = -1;
        *entered = -1;
        if (*miss) {
            if (t1.size() + b1.size() == C) {
                if (!t1.empty()) {
                    *evictee = t1_list.back();
                    *last_ref = 0; // Adjust this with actual last reference time if needed
                    *entered = 0;  // Adjust this with actual entry time if needed
                    t1_list.pop_back();
                    t1.erase(*evictee);
                } else {
                    b1_list.pop_back();
                    b1.erase(b1_list.back());
                }
                replace(addr);
            } else if (t1.size() + t2.size() + b1.size() + b2.size() >= C) {
                if (t1.size() + t2.size() + b1.size() + b2.size() == 2 * C) {
                    b2_list.pop_back();
                    b2.erase(b2_list.back());
                }
                replace(addr);
            }
        }
        access(addr);
    }

    void multi_access(int n, py::array_t<int>& addrs)
	{
		int32_t* addrs_ptr = addrs.mutable_data();

		for (int i = 0; i < n; i++)
		{
			access(addrs_ptr[i]);
		}
	}

    double hit_rate() {
        return hits / double(hits + misses);
    }

    void data(int& access_count, int& miss_count) {
        access_count = hits + misses;
        miss_count = misses;
    }
};

PYBIND11_MODULE(_arc, m) {
    py::class_<arc>(m, "arc")
        .def(py::init<int>())
        .def("access", &arc::access)
        .def("access_verbose", &arc::access_verbose)
        .def("hit_rate", &arc::hit_rate)
        .def("data", &arc::data)
        .def("multi_access", &arc::multi_access)
        ;

    m.def("arc_create", [](int C) {
        return new arc(C); 
    });
    m.def("arc_run", [](void* _a, int n, py::array_t<int32_t>& a) {
        arc* ar = (arc*)_a;
        ar->multi_access(n, a);
    });
    
    m.def("arc_hitrate", [](void* _a) {
        arc* ar = (arc*)_a;
        return ar->hit_rate();
    });
    m.def("arc_data", [](py::object _a) -> py::tuple {
        if (py::isinstance<arc>(_a)) {
            arc ar = _a.cast<arc>();
            int access_count, miss_count;
            ar.data(access_count, miss_count);
            return py::make_tuple(access_count, miss_count);
        }
        else {
            throw std::invalid_argument("Not passing arc object");
        }
    });
}
