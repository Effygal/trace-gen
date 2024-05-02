import numpy as np
# from ctypes import *
# libur = CDLL('./libunroll.so')

# (N x 2) array, rows are (len,addr) pairs
import _unroll 


def unroll(len_addr):
    l = np.array(len_addr[:, 0], dtype=np.int32)
    a = np.array(len_addr[:, 1], dtype=np.int32)
    n_out = np.sum(l)
    out = np.zeros(n_out, dtype=np.int32)
    # n = libur.unroll(c_int(len(l)), l.ctypes.data_as(c_void_p),
    #                  a.ctypes.data_as(c_void_p),
    #                  c_int(n_out), out.ctypes.data_as(c_void_p))
    n = _unroll.unroll(len(l), l, a, n_out, out)
    return out[:n]
