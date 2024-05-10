import numpy as np
import _unroll 

def unroll(len_addr):
    l = np.array(len_addr[:, 0], dtype=np.int32)
    a = np.array(len_addr[:, 1], dtype=np.int32)
    n_out = np.sum(l)
    out = np.zeros(n_out, dtype=np.int32)
    n = _unroll.unroll(len(l), l, a, n_out, out)
    return out[:n]
