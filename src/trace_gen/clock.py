from ctypes import *
import numpy as np
libclock = CDLL('./libclock.so')

libclock.clock1_hitrate.restype = c_double
libclock.clock1_create.restype = c_void_p


class clock:
    def __init__(self, C):
        self.f = libclock.clock1_create(c_int(C))
        self.C = C

    def run(self, trace):  # clock* new f; f->multi-access(n, a)
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        libclock.clock1_run(c_void_p(self.f), c_int(len(trace)),
                            trace.ctypes.data_as(c_void_p))

    def contents(self):
        val = np.zeros(self.C, dtype=np.int32)
        n = libclock.clock1_contents(
            c_void_p(self.f), val.ctypes.data_as(c_void_p))
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
        libclock.clock1_run_verbose(c_void_p(self.f), c_int(len(trace)),
                                    trace.ctypes.data_as(c_void_p),
                                    misses.ctypes.data_as(c_void_p))
        return misses

    def run_age(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        evicted = np.zeros(len(trace), dtype=np.int32)
        age1 = np.zeros(len(trace), dtype=np.int32)
        age2 = np.zeros(len(trace), dtype=np.int32)
        libclock.clock1_run_age(c_void_p(self.f), c_int(len(trace)),
                                trace.ctypes.data_as(c_void_p),
                                evicted.ctypes.data_as(c_void_p),
                                misses.ctypes.data_as(c_void_p),
                                age1.ctypes.data_as(c_void_p),
                                age2.ctypes.data_as(c_void_p))
        return [age1, age2, misses]

    def hitrate(self):
        a, m, c, r, x, y = self.data()
        return 1 - (m - self.C) / (a - c)

    def queue_raw_stats(self):
        n, s, s2 = c_int(), c_double(), c_double()
        libclock.clock1_queue_stats(
            c_void_p(self.f), byref(n), byref(s), byref(s2))
        return [n.value, s.value, s2.value]

    # returns (mean, std)
    def queue_stats(self):
        n, s, s2 = self.queue_raw_stats()
        return (s/n, np.sqrt((s2 - s*s/n)/(n-1)))

    def data(self):
        n_access = c_int()
        n_miss = c_int()
        n_cachefill = c_int()
        n_recycle = c_int()
        n_examined = c_int()
        sum_abit = c_int()
        libclock.clock1_data(c_void_p(self.f), byref(n_access), byref(n_miss),
                             byref(n_cachefill), byref(n_recycle),
                             byref(n_examined), byref(sum_abit))
        return [n_access.value, n_miss.value, n_cachefill.value,
                n_recycle.value, n_examined.value, sum_abit.value]

    def __del__(self):
        libclock.clock1_delete(self.f)
        self.f = None

class MC_item:
    def __init__(self, addr):       
        self.addr = addr
        self.enter_time = -1
        self.age = 0 
        self.hits = 0 # if !first && addr 
        self.A = 0
        self.R = 0
        self.E = 0
        self.window_copies = 0
    
        