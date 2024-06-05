"""
Trace Reconstructor
- Reconstructe synthetic traces from a (N*2) real trace;
- Sampling ird from the real trace;
- Support IRM and ird reconstruction from real traces;
- "pack_trace" function packages the original real trace into blocks before any processing;
- retrieve only good irds from the real trace, eliminating noises from first encounters.

Author: Peter Desnoyers & Yirong Wang
Date: 04/23/2024
"""

import numpy as np
from trace_gen.misc import *
import trace_gen.iad_wrapper as iad_wrapper
from trace_gen.unroll import *

class TraceReconstructor:
    def __init__(self, trace):
        self.trace = trace
        self.items, self.counts = None, None
        self.cdf = None
        self.irm_trace = None
        self.irds = None
        self.M = None
        self.ird_trace = None
        
    # def pack_trace(self):
    #     self.trace[:, 0] += 7
    #     self.trace = squash(unroll(self.trace // 8))       

    def get_counts(self):
        self.items, self.counts = np.unique(self.trace, return_counts=True)
        self.M = np.sum(self.counts > 3)

    def get_cdf(self):
        if self.counts is None:
            self.get_counts() 
        self.cdf = np.cumsum(self.counts) / len(self.trace)

    def generate_irm_trace(self, length):
        if self.cdf is None:
            self.get_cdf()
        self.irm_trace = [np.searchsorted(self.cdf, _) for _ in np.random.random(length)]
        return self.irm_trace

    def get_irds(self):
        if self.counts is None:
            self.get_cdf()
        r_single = np.sum(self.counts == 1) / len(self.trace)
        ird = iad_wrapper.iad(self.trace)
        ird = ird[ird > -1]
        n_single = int(r_single * len(ird))
        ird = np.append(ird, np.ones(n_single)*-1)
        self.irds = ird
        
    def sample_ird(self):
        if self.irds is None:
            self.get_irds()
        return np.random.choice(self.irds)
        
    def generate_ird_trace(self, length):
        if self.irds is None:
            self.get_irds()
        if self.M is None:
            self.get_M()
        self.ird_trace = gen_from_ird2(self.sample_ird, self.M, length)
        return self.ird_trace
    
    
# Example usage:
# trace_reconstructor = TraceReconstructor("your_trace_file_name")
# 
# irm_trace = trace_reconstructor.generate_irm_trace(length=10000)
# ird_trace = trace_reconstructor.generate_ird_trace(length=10000)
