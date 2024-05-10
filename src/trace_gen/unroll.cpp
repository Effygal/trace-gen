#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include <stdint.h>
#include <iostream>

namespace py = pybind11;

int unroll(int32_t n_in, py::array_t< int32_t >& len, py::array_t< int32_t >& addr,
           int32_t n_out, py::array_t< int32_t >& out) {
    const int32_t* len_ptr = len.data();
    const int32_t* addr_ptr = addr.data();
    int32_t* out_ptr = out.mutable_data();
    int i, j, k;
    for (i = j = 0; i < n_in && j < n_out; i++)
    {
        for (k = addr_ptr[i]; k < addr_ptr[i] + len_ptr[i]; k++)
            out_ptr[j++] = k;
    }
    return j;
}

PYBIND11_MODULE(_unroll, m) {
    m.def("unroll", &unroll);
}