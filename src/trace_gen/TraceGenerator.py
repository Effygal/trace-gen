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
    def __init__(self, M, n, ird_weights=None, irm_frac=None, zipf_a=None):
        '''
        M: set size of items
        n: trace length
        ird_weights: an vector of weights assigned to each IRD class
        irm_frac: fraction of the generated trace that follows IRM (item drawn from a zipf-like distribution)   
        zipf_a: parameter for the zipf distribution, only relevant if irm_frac > 0
        '''
        self.M = M
        self.n = n
        self.ird_weights = ird_weights
        self.trace = None # define the trace here
        self.zipf_a = zipf_a
        self.irm_frac =irm_frac 
    
    def assign_weights_with_skew(self, classes=5, skewness=1):
        '''
        Auto assign weight to each IRD classes, given the number of classes and the skewness on the weights.
        '''
        self.k = classes
        self.s = skewness

        # Generate random numbers with a decreasing trend
        random_numbers = [random.random() * (1 - i / classes) for i in range(classes)]

        # Scale the random numbers based on the skewness
        scaled_numbers = [x ** skewness for x in random_numbers]
        
        total = sum(scaled_numbers)
        
        normalized_numbers = [x / total for x in scaled_numbers]

        self.weights = normalized_numbers
        
        return normalized_numbers
    
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
        Sample an address from a set of different uniform distributions with weights following an inverse power Zipf distribution.
        '''
        if self.zipf_a is None:
            raise ValueError("Please assign a value to the zipf_a parameter first.")
        
        num_intervals = len(self.ird_weights)
        interval_width = self.M // num_intervals
        
        # Calculate Zipf probabilities
        p = 1.0 / np.power(np.arange(1, num_intervals + 1), self.zipf_a)
        p /= np.sum(p)  # Normalize to sum to 1
        
        # Select an interval based on Zipf probabilities
        choice_interval = np.random.choice(num_intervals, p=p)
        
        # Determine bounds of the chosen interval
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width
        
        # Sample uniformly within the chosen interval
        sample = np.random.uniform(lower_bound, upper_bound)
        
        return sample

    def generate_trace(self, ird_weights, irm_frac=0, zipf_a=1):
        '''
        Generate a synthetic trace;
        irm_frac specifies the fraction of the trace that follows IRM (item drawn from a zipf-like distribution);
        zipf_a defines the zipf-like distribution parameter, only relevant if irm_frac > 0.
        '''
        self.ird_weights = ird_weights
        self.irm_frac =irm_frac 
        self.zipf_a = zipf_a

        trace = gen_from_both(self.sample_ird, self.sample_zipf, self.M, self.n, irm_frac)
        self.trace = trace
        return trace

    def generate_trace_auto_weights(self, classes=5, skewness=1, irm_frac=0, zipf_a=1):
        '''
        Generate a synthetic trace with automatically assigned weights.
        '''
        ird_weights = self.assign_weights_with_skew(classes, skewness)
        return self.generate_trace(ird_weights, irm_frac, zipf_a)
    
   