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
    def __init__(self, M, n, ird_weights=None, zipf_frac=None, zipf_a=None):
        '''
        M: set size of items
        n: trace length
        freq_dist: item frequency distribution (zipfian, etc.)
        ird_dist: inter-reference distance distribution (hyperexponential, etc.)
        assume zipfian, 0.2 frac are to 0.8 frac addrs.
        '''
        self.M = M
        self.n = n
        self.ird_weights = ird_weights
        self.trace = None # define the trace here
        self.zipf_a = zipf_a
        self.zipf_frac = zipf_frac

    # def assign_weights(self, classes):
    #     '''
    #     Generate random parameters for the ird distribution.
    #     '''
    #     # Generate random numbers with a decreasing trend
    #     self.k = classes

    #     random_numbers = [random.random() * (1 - i / classes) for i in range(classes)]
    
    #     total = sum(random_numbers)
        
    #     # Normalize the numbers to make their sum 1
    #     normalized_numbers = np.array([x / total for x in random_numbers])

    #     self.weights = normalized_numbers
        
    #     return normalized_numbers
    
    # def assign_weights_with_skew(self, classes=5, skewness=1):
    #     '''
    #     Generate random parameters for the ird distribution with skewness.
    #     '''
    #     self.k = classes
    #     self.s = skewness
    #     # Generate random numbers with a decreasing trend
    #     random_numbers = [random.random() * (1 - i / classes) for i in range(classes)]

    #     # Scale the random numbers based on the skewness
    #     scaled_numbers = [x ** skewness for x in random_numbers]
        
    #     total = sum(scaled_numbers)
        
    #     normalized_numbers = [x / total for x in scaled_numbers]

    #     self.weights = normalized_numbers
        
    #     return normalized_numbers
    
    def sample_ird(self):
        '''
        Sample ird from the set of different uniform distributions with rates = self.weights.
        '''
        if self.ird_weights is None:
            raise ValueError("Please assign weights to the distribution first.")
        
        num_intervals = len(self.ird_weights)
        
        # width of each interval
        interval_width = self.M // num_intervals
        p = self.ird_weights

        # choose from an interval based on the p
        choice_interval = np.random.choice(num_intervals, p=p)

        # calculate the lower and upper bounds of the chosen interval
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width

        # uniformly sample from the chosen interval
        sample = np.random.uniform(lower_bound, upper_bound)
        return sample
    
    def sample_zipf(self):
        '''
        Sample addr from the set of different uniform distributions with weights with inverse power zipf_a.
        '''
        if self.zipf_a is None:
            raise ValueError("Please assign a value to the zipf_a parameter first.")
        
        num_intervals = len(self.ird_weights)
        interval_width = (self.M) // num_intervals
        p = 1.0 / np.power(np.arange(1, num_intervals+1), self.zipf_a)
        p /= np.sum(p)
        choice_interval = np.random.choice(num_intervals, p=p)
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width
        sample = np.random.uniform(lower_bound, upper_bound)
        return sample

    def generate_trace(self, ird_weights, zipf_frac, zipf_a):
        '''
        Generate a synthetic trace
        param indicates the probability of treating the sample as a reference directly, i.e., to what extent the trace is frequency-based.
        '''
        self.ird_weights = ird_weights
        self.zipf_frac = zipf_frac
        self.zipf_a = zipf_a

        # trace = gen_from_ird2(self.sample, self.M, self.n)
        trace = gen_from_both(self.sample_ird, self.sample_zipf, self.M, self.n, zipf_frac)
        self.trace = trace
        return trace
    
   