from ctypes import *
import numpy as np
import _clock

class clock:
    def __init__(self, C, K=1):
        self.f = _clock.clock1_create(C, K)
        self.C = C
        self.K = K

    def run(self, trace):  # clock* new f; f->multi-access(n, a)
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _clock.clock1_run(self.f, len(trace), trace)

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = _clock.clock1_contents(self.f, val)
        return val[:n]

    def run_parts(self, trace, n):
        a0, m0, vals = 0, 0, []
        for i in range(0, len(trace), n):
            # print('y', i, n, i*n, (i+1)*n)
            t = np.array(trace[i:i+n], dtype=np.int32)
            self.run(t)
            # code here
            a, m, c, r, x, y = self.data()
            # print('x', a,m,c,r)
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

    def run_verbose(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        _clock.clock1_run_verbose(self.f, len(trace), trace, misses)
        return misses

    def run_age(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        evicted = np.zeros(len(trace), dtype=np.int32)
        age1 = np.zeros(len(trace), dtype=np.int32)
        age2 = np.zeros(len(trace), dtype=np.int32)
        _clock.clock1_run_age(self.f, len(trace), trace, evicted, misses, age1, age2)
        return [age1, age2, misses]

    def hitrate(self):
        a, m, c, r, x, y = self.data()
        return 1 - (m - self.C) / (a - c)

    def queue_raw_stats(self):
        n, s, s2 = c_int(), c_double(), c_double()
        _clock.clock1_queue_stats(self.f, n, s, s2)
        return [n.value, s.value, s2.value]

    # returns (mean, std)
    def queue_stats(self):
        n, s, s2 = self.queue_raw_stats()
        return (s/n, np.sqrt((s2 - s*s/n)/(n-1)))

    def data(self) -> tuple:
        return _clock.clock1_data(self.f)

        
