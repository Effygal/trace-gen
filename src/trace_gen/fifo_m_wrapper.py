import numpy as np
import _fifo_m


class fifo_m:
    def __init__(self, m, strict: bool = False, lru: bool = False):
        m = list(m)
        self.m = m
        self.C = int(sum(m))
        self.f = _fifo_m.fifo_m_create(m, strict=strict, lru=lru)

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _fifo_m.fifo_m_run(self.f, len(trace), trace)

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = _fifo_m.fifo_m_contents(self.f, val)
        return val[:n]

    def hitrate(self):
        return _fifo_m.fifo_m_hitrate(self.f)

    def data(self) -> tuple:
        # returns (accesses, misses, fill_accesses, fill_misses)
        return _fifo_m.fifo_m_data(self.f)
