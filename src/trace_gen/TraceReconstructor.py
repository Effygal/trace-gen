"""
Trace Reconstructor
- Reconstructe synthetic traces from a (N*2) real trace;
- Sampling IRT from the real trace;
- Support IRM and IRT reconstruction from real traces;
- "load_trace" function packages the original real trace into blocks before any processing;
- retrieve only good IRTs from the real trace, eliminating noises from first encounters.

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
        self.load_trace()
        self.items, self.counts = np.unique(self.trace, return_counts=True)
        self.cdf = np.cumsum(self.counts) / len(self.trace)
        self.irm_trace = None
        self.irt = None
        self.M = np.sum(self.counts > 3)
        self.irt_trace = None
        
    def load_trace(self):
        self.trace[:, 0] += 7
        self.trace = squash(unroll(self.trace // 8))       
        
    def calculate_cdf(self):
        self.items, self.counts = np.unique(self.trace, return_counts=True)
        self.cdf = np.cumsum(self.counts) / len(self.trace)
        
    def generate_irm_trace(self, length):
        if self.cdf is None:
            self.calculate_cdf()
        self.irm_trace = [np.searchsorted(self.cdf, _) for _ in np.random.random(length)]
        return self.irm_trace

    # TODO: or use the following two functions to generate frequency trace, s.t we have a interface for sampling frequency.
    def sample_freq(self):
        return np.random.choice(self.items, p=self.counts/len(self.trace))
    # def generate_freq_trace(self, length):
    #     return gen_from_freq(self.sample_freq, self.M, length)

    def retrieve_good_irts(self):
        r_single = np.sum(self.counts == 1) / len(self.trace)
        irt = iad_wrapper.iad(self.trace)
        irt = irt[irt > 0]
        n_single = int(r_single * len(irt))
        self.irt = np.append(irt, np.ones(n_single)*-1)
        
    def sample_irt(self):
        if self.irt is None:
            self.retrieve_good_irts()
        return np.random.choice(self.irt)
        
    def generate_irt_trace(self, length):
        self.irt_trace = gen_from_iad2(self.sample_irt, self.M, length)
        return self.irt_trace
    
    
# Example usage:
# trace_reconstructor = TraceReconstructor("your_trace_file_name")
# 
# irm_trace = trace_reconstructor.generate_irm_trace(length=10000)
# irt_trace = trace_reconstructor.generate_irt_trace(length=10000)
