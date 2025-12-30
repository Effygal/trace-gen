import numpy as np
import _lfu


class lfu:
    def __init__(self, C):
        self.l = _lfu.lfu_create(C)
        self.C = C

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _lfu.lfu_run(self.l, len(trace), trace)

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = _lfu.lfu_contents(self.l, val)
        return val[:n]

    def hitrate(self):
        a, m, c = self.data()
        return 1 - (m - self.C) / (a - c)

    def data(self) -> tuple:
        # returns (accesses, misses, cachefill)
        return _lfu.lfu_data(self.l)
