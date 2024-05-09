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
import random

class TraceGenerator:
    def __init__(self, M, n):
        '''
        M: set size of items
        n: trace length
        freq_dist: item frequency distribution (zipfian, etc.)
        irt_dist: inter-reference time distribution (hyperexponential, etc.)
        assume zipfian, 0.2 frac are to 0.8 frac addrs.
        '''
        self.M = M
        self.n = n
        # self.items = np.arange(M)
        self.params = None
        # self.trace = None # define the trace here
                          # read/write ratio?
        self.irt = []

    def assign_params(self, classes):
        '''
        Generate random parameters for the IRT distribution.
        '''
        # Generate n random numbers between 0 and 1
        random_numbers = [random.random() for _ in range(classes)]
        
        # Calculate the sum of the random numbers
        total = sum(random_numbers)
        
        # Normalize the numbers to make their sum 1
        normalized_numbers = np.array([x / total for x in random_numbers])

        self.params = normalized_numbers
        
        return normalized_numbers
    
    def assign_params_with_skew(self, classes=5, skewness=3):
        '''
        Generate random parameters for the IRT distribution with skewness;
        Empirically we observe 5 classes and skewness of 3 works well.
        '''

        # Generate n random numbers between 0 and 1
        random_numbers = [random.random() for _ in range(classes)]
        
        # Scale the random numbers based on the skewness
        scaled_numbers = [x ** skewness for x in random_numbers]
        
        # Calculate the sum of the scaled random numbers
        total = sum(scaled_numbers)
        
        # Normalize the scaled numbers to make their sum 1
        normalized_numbers = [x / total for x in scaled_numbers]

        random.shuffle(normalized_numbers)

        self.params = normalized_numbers
        
        return normalized_numbers
    
    def sample_irt(self):
        '''
        Sample irt from the set of different uniform distributions with rates = self.params.
        '''
        num_intervals = len(self.params)
        
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

    def generate_trace(self, classes, skewness=0):
        '''
        Generate a synthetic trace
        '''
        # self.assign_params_with_skew(classes, skewness)
        self.assign_params(classes)
        trace = gen_from_iad2(self.sample_irt, self.M, self.n)
        # self.trace = trace
        return trace
