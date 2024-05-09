from ctypes import *
import numpy as np
# libfifo = CDLL('./libfifo.so')
import _fifo
# libfifo.fifo_hitrate.restype = c_double
# libfifo.fifo_create.restype = c_void_p

class fifo:
    def __init__(self, C):
        # self.f = libfifo.fifo_create(c_int(C))
        self.f = _fifo.fifo_create(C)
        self.C = C

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        # libfifo.fifo_run(c_void_p(self.f), c_int(len(trace)),
        #                      trace.ctypes.data_as(c_void_p))
        _fifo.fifo_run(self.f, len(trace), trace)

    def contents(self):
        val = np.zeros(self.C,dtype=np.int32)
        # n = libfifo.fifo_contents(c_void_p(self.f), val.ctypes.data_as(c_void_p))
        n = _fifo.fifo_contents(self.f, val)
        return val[:n]

    def run_verbose(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        # libfifo.fifo_run_verbose(c_void_p(self.f), c_int(len(trace)),
        #                              trace.ctypes.data_as(c_void_p),
        #                              misses.ctypes.data_as(c_void_p))
        _fifo.fifo_run_verbose(self.f, len(trace), trace, misses)
        return misses

    def run_age(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        misses = np.zeros(len(trace), dtype=np.int32)
        ages = np.zeros(len(trace), dtype=np.int32)
        # libfifo.fifo_run_age(c_void_p(self.f), c_int(len(trace)),
                                #  trace.ctypes.data_as(c_void_p),
                                #  misses.ctypes.data_as(c_void_p),
                                #  ages.ctypes.data_as(c_void_p))
        _fifo.fifo_run_age(self.f, len(trace), trace, misses, ages)
        return [ages, misses]
    
    def hitrate(self):
        a,m,c = self.data()
        return 1 - (m - self.C) / (a - c)
    
    def data(self):
        return _fifo.fifo_data(self.f)
        # n_access = c_int()
        # n_miss = c_int()
        # n_cachefill = c_int()
        # libfifo.fifo_data(c_void_p(self.f), byref(n_access), byref(n_miss),
        #                       byref(n_cachefill))
        # return [n_access.value, n_miss.value, n_cachefill.value]

    def queue_raw_stats(self):
        n,s,s2 = c_int(),c_double(),c_double()
        # libfifo.fifo_queue_stats(c_void_p(self.f), byref(n), byref(s), byref(s2))
        _fifo.fifo_queue_stats(self.f, n, s, s2)
        return [n.value,s.value,s2.value]

    # returns (mean, std)
    def queue_stats(self):
        n,s,s2 = self.queue_raw_stats()
        return (s/n, np.sqrt((s2 - s*s/n)/(n-1)))

    # def __del__(self):
    #     libfifo.fifo_delete(c_void_p(self.f))
