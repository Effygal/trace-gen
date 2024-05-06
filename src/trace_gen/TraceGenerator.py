"""
Trace Generator
- Generate synthetic traces from a set of parameters;
- Sampling IRT from the real trace;
Author: Peter Desnoyers & Yirong Wang
Date: 04/23/2024
"""
import numpy as np
from trace_gen.misc import *
import trace_gen.iad_wrapper as iad_wrapper
from trace_gen.unroll import *

class TraceGenerator:
    def __init__(self, M, n, r_w_ratio = 0.5, params = np.array([0.2, 0.8])):
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
        self.params = params
        self.num_classes = len(params)
        self.trace = None # define the trace here
                          # read/write ratio?
        self.irt = []
    
    def sample_irt(self):
        '''
        Sample irt from the set of different uniform distributions with rates = self.params.
        '''
        num_intervals = self.num_classes
        
        # Calculate the width of each interval
        interval_width = (self.M) / num_intervals

        # Choose an interval based on the probabilities
        choice = np.random.choice(num_intervals, p=self.params)

        # Calculate the lower and upper bounds of the chosen interval
        lower_bound = choice * interval_width
        upper_bound = (choice + 1) * interval_width

        # Sample from the chosen uniform interval
        irt = np.random.uniform(lower_bound, upper_bound)  
        self.irt.append(irt)
        return int(irt)

    def generate_trace(self):
        '''
        Generate a synthetic trace
        '''
        trace = gen_from_iad2(self.sample_irt, self.M, self.n)
        self.trace = trace
        return trace
