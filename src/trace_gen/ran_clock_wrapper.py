from ctypes import c_double, c_int
import numpy as np
import _ran_clock


class ran_clock:
    def __init__(self, C):
        self.f = _ran_clock.ran_clock_create(C)
        self.C = C

    def run(self, trace, rp=True):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _ran_clock.ran_clock_run(self.f, len(trace), trace, rp)

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = _ran_clock.ran_clock_contents(self.f, val)
        return val[:n]

    def run_parts(self, trace, n, rp=True):
        a0, m0, vals = 0, 0, []
        for i in range(0, len(trace), n):
            t = np.array(trace[i:i+n], dtype=np.int32)
            self.run(t, rp)
            a, m, c, r, x, y = self.data()
            vals.append(1 - (m - m0)/(a - a0))
            a0, m0 = a, m
        return np.array(vals)

    def run_slices(self, trace, n, rp=True):
        sliced_contents = []
        for i in range(0, len(trace), n):
            t = np.array(trace[i:i+n], dtype=np.int32)
            self.run(t, rp)
            contents = self.contents()
            sliced_contents.append(contents)
        return sliced_contents

    def run_age(self, trace, rp=True):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        evicted = np.zeros(len(trace), dtype=np.int32)
        age1 = np.zeros(len(trace), dtype=np.int32)
        age2 = np.zeros(len(trace), dtype=np.int32)
        _ran_clock.ran_clock_run_age(self.f, len(trace), trace, evicted, misses, age1, age2, rp)
        return [age1, age2, misses]

    def hitrate(self):
        a, m, c, r, x, y = self.data()
        return 1 - (m - self.C) / (a - c)

    def queue_raw_stats(self):
        n, s, s2 = c_int(), c_double(), c_double()
        _ran_clock.ran_clock_queue_stats(self.f, n, s, s2)
        return [n.value, s.value, s2.value]

    def queue_stats(self):
        n, s, s2 = self.queue_raw_stats()
        return (s/n, np.sqrt((s2 - s*s/n)/(n-1)))

    def data(self):
        return _ran_clock.ran_clock_data(self.f)
