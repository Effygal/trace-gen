# misc functions for simulating hot/cold traffic, resampling, etc.
#

import pickle
import trace_gen.lru_wrapper as lru_wrapper
# import clock
import trace_gen.fifo_wrapper as fifo
import heapq
import numpy as np
import random


def hc(r, f, M):
    if random.random() < r:
        return random.randint(0, int(f*M)-1)
    else:
        return random.randint(int(f*M), M-1)


def hc_trace(r, f, M, n):
    trc = np.zeros(n, dtype=np.int32)
    for i in range(n):
        if random.random() < r:
            trc[i] = random.randint(0, int(f*M)-1)
        else:
            trc[i] = random.randint(int(f*M), M-1)
    return trc


def t_hc(r, f, M):
    if random.random() < r:
        return random.expovariate(r/(f*M)), True
    else:
        return random.expovariate((1-r)/((1-f)*M)), False

def gen_he(r,f,M,n):
    h = []
    for i in range(M):
        if random.random() < r:
            t = random.expovariate(r/(f*M))
        else:
            t = random.expovariate((1-r)/((1-f)*M))
        heapq.heappush(h, [t,i])        
    a = []
    is_hot = []
    for i in range(n):
        t0,addr = h[0]
        a.append(addr)
        if random.random() < r:
            is_hot.append(True)
            t = random.expovariate(r/(f*M))
        else:
            is_hot.append(False)
            t = random.expovariate((1-r)/((1-f)*M))
        heapq.heapreplace(h, [t0+t,addr])
    return np.array(a, dtype=np.int32), np.array(is_hot, dtype=bool)
# trc,is_hot = gen_he(r,f,M,14*M)

def gen_from_iad(f, M, n):
    h = []
    for i in range(M):
        # code changed here:
        t = f()[0]
        heapq.heappush(h, [t, i])
    a = []
    for i in range(n):
        t0, addr = h[0]
        a.append(addr)
        t = f()[0]
        heapq.heapreplace(h, [t0+t, addr])
    return np.array(a, dtype=np.int32)
# 2 outputs f() must return a tuple (val, bool).

def gen_from_iad2(f, largest_address, number_of_samples):
    """
    f is a function that returns a pair of (addr: int, is_hot_or_cold: bool)
    """
    h = []
    a0 = 0
    # push all [t, hot_flag, a0] pair to the heap h, where t is drawn from the distribution function f();
    while len(h) < largest_address:
        t = f()
        if t != -1:
            # assign an addr to each drawn t
            heapq.heappush(h, [t, a0])
            a0 += 1

    addrs = []
    for _ in range(number_of_samples):  # create trace
        t = f()
        if t == -1:  # this clause won't be triggered for a synthetic trace.
            # assign a new addr that is not on the heap i.e. the map.
            addrs.append(a0)
            a0 += 1

        else:  # if there are references before, append the lowest addr to a, update time track with t0+t;
            t0, addr = h[0]
            addrs.append(addr)
            heapq.heapreplace(h, [t0+t, addr])

    # return List[address: int], List[hot_or_cold: bool]
    return np.array(addrs, dtype=np.int32)


def sim_fifo(C, trace, raw=False):
    f = fifo.fifo(C)
    f.run(trace)
    if raw:
        a, m, c = f.data()
        return 1 - m/a
    else:
        return f.hitrate()


# def sim_clock(C, trace, raw=False):
#     c = clock.clock(C)
#     c.run(trace)
#     if raw:
#         # variable name c used for two different thing?
#         a, m, cf, recycle, examined, sumabit = c.data()
#         return 1 - m/a
#     else:
#         return c.hitrate()


def sim_lru(C, trace, raw=False):
    l = lru_wrapper.lru(C)
    l.run(trace)
    if raw:
        a, m, c = l.data()
        return 1 - m/a
    else:
        return l.hitrate()

# "compact" the address space of a trace.


def squash(t):
    a = np.unique(t)
    n = np.zeros(np.max(t)+1, dtype=np.int32)
    x = np.arange(len(a), dtype=np.int32)
    n[a] = x
    return n[t]


def from_pickle(f):
    fp = open(f, 'rb')
    val = pickle.load(fp)
    fp.close()
    return val


def to_pickle(var, f):
    fp = open(f, 'wb')
    pickle.dump(var, fp)
    fp.close()
