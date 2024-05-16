"""
Trace Generator
- Generate synthetic traces from a set of parameters;
- Sampling ird from the real trace;
Author: Peter Desnoyers & Yirong Wang
Date: 04/23/2024
"""
import numpy as np
from trace_gen.misc import *
# import trace_gen.iad_wrapper as iad_wrapper
# from trace_gen.unroll import *
import random

class TraceGenerator:
    def __init__(self, M, n):
        '''
        M: set size of items
        n: trace length
        freq_dist: item frequency distribution (zipfian, etc.)
        ird_dist: inter-reference distance distribution (hyperexponential, etc.)
        assume zipfian, 0.2 frac are to 0.8 frac addrs.
        '''
        self.M = M
        self.n = n
        # self.items = np.arange(M)
        self.weights = None
        # self.trace = None # define the trace here
                          # read/write ratio?
        self.ird = []

    def assign_weights(self, classes):
        '''
        Generate random parameters for the ird distribution.
        '''
        # Generate random numbers with a decreasing trend
        random_numbers = [random.random() * (1 - i / classes) for i in range(classes)]
    
        total = sum(random_numbers)
        
        # Normalize the numbers to make their sum 1
        normalized_numbers = np.array([x / total for x in random_numbers])

        self.weights = normalized_numbers
        
        return normalized_numbers
    
    def assign_weights_with_skew(self, classes=5, skewness=3):
        '''
        Generate random parameters for the ird distribution with skewness.
        '''

        # Generate random numbers with a decreasing trend
        random_numbers = [random.random() * (1 - i / classes) for i in range(classes)]
        
        # Scale the random numbers based on the skewness
        scaled_numbers = [x ** skewness for x in random_numbers]
        
        total = sum(scaled_numbers)
        
        normalized_numbers = [x / total for x in scaled_numbers]

        self.weights = normalized_numbers
        
        return normalized_numbers
    
    def sample(self):
        '''
        Sample ird from the set of different uniform distributions with rates = self.weights.
        '''
        num_intervals = len(self.weights)
        
        # Calculate the width of each interval
        interval_width = (self.M) / num_intervals

        # Choose an interval based on the probabilities
        choice = np.random.choice(num_intervals, p=self.weights)

        # Calculate the lower and upper bounds of the chosen interval
        lower_bound = choice * interval_width
        upper_bound = (choice + 1) * interval_width

        # Sample from the chosen uniform interval
        ird = np.random.uniform(lower_bound, upper_bound)  
        self.ird.append(ird)
        return np.array(ird, dtype=np.int32)

    def generate_trace(self, classes, skewness=1, param=0):
        '''
        Generate a synthetic trace
        param indicates the probability of treating the sample as a reference directly, i.e., to what extent the trace is frequency-based.
        '''
        self.assign_weights_with_skew(classes, skewness)

        # trace = gen_from_ird2(self.sample, self.M, self.n)
        trace = gen_from_both(self.sample, self.M, self.n, param)
        # self.trace = trace
        return trace
