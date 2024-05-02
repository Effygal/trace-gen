"""
Trace Generator
- Generate synthetic traces from a set of parameters;
- Sampling IRT from the real trace;
- TODO: slice according to item frequency;
        each slice generate a trace from irt distribution;


Author: Peter Desnoyers & Yirong Wang
Date: 04/23/2024
"""
import numpy as np
from trace_gen.misc import *
import trace_gen.iad_wrapper as iad_wrapper
from trace_gen.unroll import *

class TraceGenerator:
    def __init__(self, M, n, r_w_ratio = 0.5, poisson_params = np.array([0.2, 0.8])):
        '''
        M: set size of items
        n: trace length
        freq_dist: item frequency distribution (zipfian, etc.)
        irt_dist: inter-reference time distribution (hyperexponential, etc.)
        assume zipfian, 0.2 frac are to 0.8 frac addrs.
        '''
        self.M = M
        self.n = n
        self.items = np.arange(M)
        self.r_w_ratio = r_w_ratio
        self.poisson_param = poisson_params
        self.num_classes = len(poisson_params)
        self.trace = None # define the trace here
                          # read/write ratio?
    
    def sample_irt(self):
        '''
        Sample irt from the freq distribution
        '''
        rate_lambda = np.random.choice(self.poisson_param, p=np.flip(self.poisson_param))
        irt = np.random.exponential(scale=1/rate_lambda)
        return int(irt)

    def generate_trace(self):
        '''
        Generate a synthetic trace
        '''
        trace = gen_from_iad2(self.sample_irt, self.M, self.n)
        return trace
    
