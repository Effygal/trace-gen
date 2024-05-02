from ctypes import *
import numpy as np
# liblru = CDLL('./liblru.so')
import _lru


class lru:
    def __init__(self, C):
        # self.l = liblru.lru_create(c_int(C))
        self.l = _lru.lru_create(C)
        self.C = C

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        # liblru.lru_run(c_void_p(self.l), c_int(len(trace)),
        #                trace.ctypes.data_as(c_void_p))
        _lru.lru_run(self.l, len(trace), trace)

    def run_age(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        evicted = np.zeros(len(trace), dtype=np.int32)
        age1 = np.zeros(len(trace), dtype=np.int32)
        age2 = np.zeros(len(trace), dtype=np.int32)
        # liblru.lru_run_age(c_void_p(self.l), c_int(len(trace)),
        #                    trace.ctypes.data_as(c_void_p),
        #                    misses.ctypes.data_as(c_void_p),
        #                    evicted.ctypes.data_as(c_void_p),
        #                    age1.ctypes.data_as(c_void_p),
        #                    age2.ctypes.data_as(c_void_p))
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
        # n = liblru.lru_contents(c_void_p(self.l), val.ctypes.data_as(c_void_p))
        n = _lru.lru_contents(self.l, val)
        return val[:n]

    def hitrate(self):
        a, m, c = self.data()
        return 1 - (m - self.C) / (a - c)

    def data(self) -> tuple:
        return _lru.lru_data(self.l)
        # n_access = 0 # c_int()
        # n_miss = 0 # c_int()
        # n_cachefill = 0 # c_int()
        # _lru.lru_data(self.l, n_access, n_miss, n_cachefill)
        #             #   byref(n_access), byref(n_miss),
        #                 # byref(n_cachefill))
        # print(n_access, n_miss, n_cachefill)
        
        # return [n_access, n_miss, n_cachefill]

    def queue_raw_stats(self):
        n, s, s2 = c_int(), c_double(), c_double()
        # liblru.lru_queue_stats(c_void_p(self.l), byref(n), byref(s), byref(s2))
        _lru.lru_queue_stats(self.l, byref(n), byref(s), byref(s2))
        return [n.value, s.value, s2.value]

    def queue_stats(self):
        n, s, s2 = self.queue_raw_stats()
        return (s/n, np.sqrt((s2 - s*s/n)/(n-1)))

    # def __del__(self):
    #     # liblru.lru_delete(c_void_p(self.l))
    #     _lru.lru_delete(self.l)
