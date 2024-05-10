from ctypes import *
import numpy as np
import _lru


class lru:
    def __init__(self, C):
        self.l = _lru.lru_create(C)
        self.C = C

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _lru.lru_run(self.l, len(trace), trace)

    def run_age(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        evicted = np.zeros(len(trace), dtype=np.int32)
        age1 = np.zeros(len(trace), dtype=np.int32)
        age2 = np.zeros(len(trace), dtype=np.int32)
        _lru.lru_run_age(self.l, len(trace), trace, misses, evicted, age1, age2)
        return [age1, age2, misses]

    def run_parts(self, trace, n):
        a0, m0, vals = 0, 0, []
        for i in range(0, len(trace), n):
            t = np.array(trace[i:i+n], dtype=np.int32)
            self.run(t)
            a, m, c = self.data()
            vals.append(1 - (m-m0)/(a-a0))
            a0, m0 = a, m
        return np.array(vals)

    # run slice to get contents: return a list of cache states.
    def run_slices(self, trace, n):
        sliced_contents = []
        for i in range(0, len(trace), n):
            # print('y', i, n, i*n, (i+1)*n)
            t = np.array(trace[i:i+n], dtype=np.int32)
            self.run(t)
            contents = self.contents()
            sliced_contents.append(contents)
        return sliced_contents

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = _lru.lru_contents(self.l, val)
        return val[:n]

    def hitrate(self):
        a, m, c = self.data()
        return 1 - (m - self.C) / (a - c)

    def data(self) -> tuple:
        return _lru.lru_data(self.l)

    def queue_raw_stats(self):
        n, s, s2 = c_int(), c_double(), c_double()
        _lru.lru_queue_stats(self.l, byref(n), byref(s), byref(s2))
        return [n.value, s.value, s2.value]

    def queue_stats(self):
        n, s, s2 = self.queue_raw_stats()
        return (s/n, np.sqrt((s2 - s*s/n)/(n-1)))

