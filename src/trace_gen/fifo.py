from ctypes import *
import numpy as np
libfifo = CDLL('./libfifo.so')

libfifo.fifo_hitrate.restype = c_double
libfifo.fifo_create.restype = c_void_p

class fifo:
    def __init__(self, C):
        self.f = libfifo.fifo_create(c_int(C))
        self.C = C

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        libfifo.fifo_run(c_void_p(self.f), c_int(len(trace)),
                             trace.ctypes.data_as(c_void_p))

    def contents(self):
        val = np.zeros(self.C,dtype=np.int32)
        n = libfifo.fifo_contents(c_void_p(self.f), val.ctypes.data_as(c_void_p))
        return val[:n]

    def run_verbose(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        libfifo.fifo_run_verbose(c_void_p(self.f), c_int(len(trace)),
                                     trace.ctypes.data_as(c_void_p),
                                     misses.ctypes.data_as(c_void_p))
        return misses

    def run_age(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        ages = np.zeros(len(trace), dtype=np.int32)
        libfifo.fifo_run_age(c_void_p(self.f), c_int(len(trace)),
                                 trace.ctypes.data_as(c_void_p),
                                 misses.ctypes.data_as(c_void_p),
                                 ages.ctypes.data_as(c_void_p))
        return [ages,misses]
    
    def hitrate(self):
        a,m,c = self.data()
        return 1 - (m - self.C) / (a - c)
    
    def data(self):
        n_access = c_int()
        n_miss = c_int()
        n_cachefill = c_int()
        libfifo.fifo_data(c_void_p(self.f), byref(n_access), byref(n_miss),
                              byref(n_cachefill))
        return [n_access.value, n_miss.value, n_cachefill.value]

    def queue_raw_stats(self):
        n,s,s2 = c_int(),c_double(),c_double()
        libfifo.fifo_queue_stats(c_void_p(self.f), byref(n), byref(s), byref(s2))
        return [n.value,s.value,s2.value]

    # returns (mean, std)
    def queue_stats(self):
        n,s,s2 = self.queue_raw_stats()
        return (s/n, np.sqrt((s2 - s*s/n)/(n-1)))

    def __del__(self):
        libfifo.fifo_delete(c_void_p(self.f))
