import numpy as np
from ctypes import *
libqfifo = CDLL('./libqfifo.so')


class fifo:
    def __init__(self, C, M):
        self.f = libqfifo.fifo_create(c_int(C), c_int(M))
        self.C = C

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        libqfifo.fifo_run(self.f, c_int(len(trace)),
                          trace.ctypes.data_as(c_void_p))

    def hitrate(self):
        a, m, c = self.data()
        return 1 - (m - self.C) / (a - c)

    def data(self):
        n_access = c_int()
        n_miss = c_int()
        n_cachefill = c_int()
        libqfifo.fifo_data(self.f, byref(n_access), byref(n_miss),
                           byref(n_cachefill))
        return [n_access.value, n_miss.value, n_cachefill.value]

    def logs(self):
        a, m, c = self.data()
        hits = np.zeros(a, dtype=np.int32)
        age = np.zeros(a, dtype=np.int32)
        posn = np.zeros(a, dtype=np.int32)
        n = libqfifo.fifo_log(self.f, c_int(a),
                              hits.ctypes.data_as(c_void_p),
                              age.ctypes.data_as(c_void_p),
                              posn.ctypes.data_as(c_void_p))
        return np.stack((hits[:n], age[:n], posn[:n]), axis=1)


class queue:
    def __init__(self):
        self.size = 0
        self.lists = []
        self.newest = []
        self.oldest = []

    def count(self):
        return self.size

    def add(self, val):
        self.newest.append(val)
        self.size += 1
        if len(self.newest) > 500:
            self.lists.append(self.newest)
            self.newest = []

    def remove(self):
        if len(self.oldest) == 0:
            self.oldest = self.lists.pop(0)
        v = self.oldest.pop(0)
        self.size -= 1
        return v


class old_fifo:
    def __init__(self, C, M):
        self.Q = queue()
        self.C = C
        self.lastmiss = np.zeros(M, dtype=np.int32)
        self.lastref = np.zeros(M, dtype=np.int32)
        self.d = np.zeros(M, dtype=np.int8)
        self.misses = 0
        self.n = 0
        self.log = []
        self.evicts = []

    def access(self, a):
        self.n += 1
        age, posn, hit = 0, 0, 0
        if self.lastref[a]:
            age = self.n - self.lastref[a]
        # if self.lastmiss[a]:
            # assert(self.misses >= self.lastmiss[a])
            # posn = self.misses - self.lastmiss[a]
        if self.d[a]:
            hit = 1
        else:
            self.misses += 1
            self.lastmiss[a] = self.n
            if self.Q.count() >= self.C:
                b = self.Q.remove()
                self.evicts.append(self.n - self.lastmiss[b])
                self.d[b] = 0
            self.Q.add(a)
            self.d[a] = 1
        self.log.append([hit, age, posn])
        self.lastref[a] = self.n

    def run(self, trace):
        for a in trace:
            self.access(a)

    def stats(self):
        return self.n, self.misses
