import numpy as np
import _min


class belady_min:
    def __init__(self, C):
        self.C = C
        self.m = _min.min_create(C)

    def run(self, trace):
        if len(trace) == 0:
            return
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _min.min_run(self.m, len(trace), trace)

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = _min.min_contents(self.m, val)
        return val[:n]

    def data(self):
        return _min.min_data(self.m)

    def hitrate(self):
        a, m, c = self.data()
        denom = (a - c) if (a - c) > 0 else a if a > 0 else 1
        return 1 - (m - self.C) / denom
