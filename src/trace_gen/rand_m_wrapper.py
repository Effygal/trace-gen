import numpy as np
import _rand_m


class rand_m:
    def __init__(self, m):
        m = list(m)
        self.m = m
        self.C = int(sum(m))
        self.r = _rand_m.rand_m_create(m)

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _rand_m.rand_m_run(self.r, len(trace), trace)

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = _rand_m.rand_m_contents(self.r, val)
        return val[:n]

    def hitrate(self):
        return _rand_m.rand_m_hitrate(self.r)

    def data(self) -> tuple:
        # returns (accesses, misses, fill_accesses, fill_misses)
        return _rand_m.rand_m_data(self.r)
