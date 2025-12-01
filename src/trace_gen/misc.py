# misc functions for simulating hot/cold traffic, resampling, etc.

import pickle
import trace_gen.lru_wrapper as lru
import trace_gen.fifo_wrapper as fifo
import trace_gen.clock_wrapper as clock
import trace_gen.sieve_wrapper as sieve
# import trace_gen.arc_wrapper as arc
import trace_gen.ran_clock_wrapper as ran_clock
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

def gen_from_ird(f, M, n):
    """
    f is a function returns a tuple (addr: int, is_hot: bool)
    """
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

def gen_from_ird2(f, M, n):
    h = []
    a0 = 0
    while len(h) < M:
        t = f()
        if t != -1:
            heapq.heappush(h, [t, a0])
            a0 += 1

    addrs = []
    for _ in range(n):  
        t = f()
        if t == -1: 
            addrs.append(a0)
            a0 += 1
        else:  
            t0, addr = h[0]
            addrs.append(addr)
            heapq.heapreplace(h, [t0+t, addr])
    return np.array(addrs, dtype=np.int32)

def gen_from_both(f, g,  M, n, irm_frac=0):
    h = []
    a0 = 0

    while len(h) < M:
        t = f()
        if t != -1:
            heapq.heappush(h, [t, a0])
            a0 += 1

    addrs = []
    count = 0
    for _ in range(n): 
        if random.random() < irm_frac: 
            a = g()
            addrs.append(a) 
        else:
            t = f()
            if t == -1:  
                addrs.append(a0)
                a0 += 1
            else:  
                t0, addr = h[0]
                addrs.append(addr)
                heapq.heapreplace(h, [t0+t, addr])
        count += 1

    return np.array(addrs, dtype=np.int32)

def gen_from_both_verbose(f, g,  M, n, irm_frac=0):
    h = []
    a0 = 0
    while len(h) < M:
        t = f()
        if t != -1:
            heapq.heappush(h, [t, a0])
            a0 += 1
    addrs = []
    is_irm = []
    time_var = []
    count = 0
    for _ in range(n):
        if random.random() < irm_frac: 
            a = g()
            addrs.append(a) 
            is_irm.append(True)
        else:
            t = f()
            if t == -1:  
                addrs.append(a0)
                a0 += 1
            else:  
                t0, addr = h[0]
                addrs.append(addr)
                heapq.heapreplace(h, [t0+t, addr])
            is_irm.append(False)
            time_var.append(t0-count)
        count += 1
    return np.array(addrs, dtype=np.int32), np.array(is_irm, dtype=bool), np.array(time_var, dtype=np.int32)

def sim_fifo(C, trace, raw=True):
    f = fifo.fifo(C)
    f.run(trace)
    if raw:
        a, m, c = f.data()
        return 1 - m/a
    else:
        return f.hitrate()

def sim_clock(C, trace, raw=True):
    c = clock.clock(C)
    c.run(trace)
    if raw:
        a, m, cf, recycle, examined, sumabit = c.data()
        return 1 - m/a
    else:
        return c.hitrate()

def sim_lru(C, trace, raw=True):
    l = lru.lru(C)
    l.run(trace)
    if raw:
        a, m, c = l.data()
        return 1 - m/a
    else:
        return l.hitrate()

def sim_ran_clock(C, trace, raw=True, rp=True, K=1):
    rc = ran_clock.ran_clock(C, K=K)
    rc.run(trace, rp=rp)
    if raw:
        a, m, c, r, x, y = rc.data()
        return 1 - m/a
    else:
        return rc.hitrate() 

def sim_sieve(C, trace, raw=True):
    s = sieve.sieve(C)
    s.run(trace)
    if raw:
        a, m, *_ = s.data()
        return 1 - m/a
    else:
        return s.hitrate()
    
# def sim_arc(C, trace, raw=True):
#     a = arc.arc(C)
#     a.run(trace)
#     if raw:
#         a, m = a.data()
#         return 1 - m/a
#     else:
#         return a.hitrate()

# "compact" the address space of a trace.
def squash(t):
    a = np.unique(t)
    n = np.zeros(np.max(t)+1, dtype=np.int64)
    x = np.arange(len(a), dtype=np.int64)
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

def fgen(k, indices, eps=1e-6):
    l = np.full(k, eps)  
    l[indices] = (1 - eps) / len(indices) 
    l = l / l.sum()
    return l
