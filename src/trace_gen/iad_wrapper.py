from ctypes import *
import numpy as np
import _iad

class iad2:
    def __init__(self, _max):
        self.max = _max
        self.times = np.zeros(_max+1, dtype=np.int32)
        self.t = 1

    def recency(self):
        b = self.times[self.times > 0]
        return self.t - b

    def run(self, trace):
        vals = np.zeros(len(trace), dtype=np.int32)
        n = len(trace)
        t = c_int(self.t)
        if type(trace[0]) != np.int32:
            trace = np.array(trace, np.int32)
        rv = _iad.iad2(self.max, n, trace, vals, t, self.times)
        assert rv, '%d' % rv
        self.t = t.value
        return vals


def iad(trace):
    n = len(trace)
    m = np.max(trace) + 1
    if type(trace[0]) != np.int32:
        trace = np.array(trace, np.int32)
    val = np.zeros(n, dtype=np.int32)
    _iad.iad(m, n, trace, val)
    return val
