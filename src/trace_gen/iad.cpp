#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

int iad(int32_t max, int32_t n, py::array_t< int32_t >& in, py::array_t< int32_t >& out)
{
    const int32_t* in_ptr = in.data();
    int32_t* out_ptr = out.mutable_data();
    int32_t *T = (int32_t *)calloc(1, sizeof(int32_t) * (uint64_t)max);
    int32_t t = 1;
    for (int i = 0; i < n; i++)
    {
        int32_t a = in_ptr[i];
        if (a >= max)
        {
            printf("ERROR: a[%d] = %d (max %d)\n", i, a, max);
            break;
        }
        if (T[a] == 0)
            out_ptr[i] = -1;
        else
            out_ptr[i] = t - T[a];
        T[a] = t;
        t++;
    }
    free(T);
    return 1;
}

int iad2(int32_t max, int32_t n, py::array_t< int32_t >& in, py::array_t< int32_t >& out,
         py::array_t< int32_t >& t, py::array_t< int32_t >& T)
{
    const int32_t* in_ptr = in.data();
    int32_t* out_ptr = out.mutable_data();
    int32_t* t_ptr = t.mutable_data();
    int32_t* T_ptr = T.mutable_data();
    for (int i = 0; i < n; i++)
    {
        int32_t a = in_ptr[i];
        if (a >= max)
            return 0;
        if (T_ptr[a] == 0)
            out_ptr[i] = -1;
        else
            out_ptr[i] = *t_ptr - T_ptr[a];
        T_ptr[a] = *t_ptr;
        (*t_ptr)++;
    }
    return 1;
}

PYBIND11_MODULE(_iad, m) {
    m.def("iad", &iad);
    m.def("iad2", &iad2);
}