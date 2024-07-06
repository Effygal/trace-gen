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
        weights: an vector of weights assigned to each IRD (IRM) class
        irm_frac: fraction of the generated trace that follows IRM (item drawn from a zipf-like distribution)   
        zipf_a: parameter for the zipf distribution, only relevant if irm_frac > 0
        '''
        self.M = M
        self.n = n
        self.weights = [0.79992, 0.0001, 0.19998] # default weights for IRD
        self.zipf_a = 1.2 # exponent parameter for the zipf distribution
        self.p_irm = 0 # fraction of the trace that follows IRM
        self.ird_k = 3 # num of classes for IRD
        self.ird_s = 4 # skewness of the IRD weights
        self.irm_k = 3 # num of classes for IRM
        self.pareto_a = 2.5 # the shape paremeter of pareto_alpha
        self.pareto_xm = 1 # the scale parameter pareto_xm
        
    # define setters:
    def set_zipf_a(self, a):
        self.zipf_a = a
    
    def set_pareto_a(self, a):
        self.pareto_a = a
    
    def set_xm(self, xm):
        self.pareto_xm = xm
    
    def set_p_irm(self, frac):
        self.p_irm = frac
    
    def set_ird_k(self, k):
        self.ird_k = k
    
    def set_ird_s(self, s):
        self.ird_s = s
    
    def set_irm_k(self, k):
        self.irm_k = k

    def assign_3_weights(self, s=4):
        '''
        Assign weights to the IRD classes with default k=2.
        s is the ratio of the weights of the first and last class.
        '''
        self.s = s
        self.k = 3 # only happens when k = 3
        middle = 1 / (10 ** s) #create a hole
        r = 1 - middle #the rest
        last= r / (self.s + 1)
        first = self.s * last
        weights = [first, middle, last]
        self.weights = weights
        return weights
    
    def assign_k_weights(self, classes):
        '''
        Assign weights to the IRD classes with default s=2.
        k is the number of classes.
        '''
        self.k = classes
        random_numbers = [random.random() * (1 - i / classes) for i in range(classes)]
        scaled_numbers = [x ** self.s for x in random_numbers]
        total = sum(scaled_numbers)
        normalized_numbers = [x / total for x in scaled_numbers]
        self.weights = normalized_numbers
        return normalized_numbers
    
    def assign_weights_with_k_s(self, classes=3, skewness=2):
        '''
        Auto assign weight to each IRD classes, given the number of classes and the skewness on the weights.
        '''
        self.k = classes
        self.s = skewness

        # Generate random numbers with a decreasing trend (heuristic, unfounded)
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
        if self.weights is None:
            raise ValueError("Please assign weights to the distribution first.")
        
        num_intervals = len(self.weights)
        
        # width of each interval
        interval_width = self.M // num_intervals
        p =self.weights 

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
        Sample an address from a set of different uniform distributions with weights following an inverse power Zipf-like distribution.
        '''
        if self.irm_k is None:
            raise ValueError("Please assign a value to the irm_k parameter first.")
        if self.zipf_a is None:
            raise ValueError("Please assign a value to the zipf_a parameter first.")
        
        num_intervals = self.irm_k
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


    def sample_pareto(self):
        """
        Generate samples from a Pareto distribution, use inverse transform sampling (given an u, receive an x s.t. F(x) >= u).

        Parameters:
        - alpha: shape parameter of the Pareto distribution.
        - xm: scale parameter of the Pareto distribution (default is 1).
        - fix sample size = 1.
        Returns:
        - a sample drawn from the Pareto distribution.
        """
        if self.pareto_a is None:
            raise ValueError("Please assign a value to the pareto_a parameter first.")
        if self.pareto_xm is None:
            raise ValueError("Please assign a value to the pareto_xm parameter first.")
        
        # Generate a uniform random sample between 0 and 1
        uniform_sample = np.random.uniform(0, 1)
        
        # Use the inverse CDF (quantile function) of the Pareto distribution
        pareto_sample = self.pareto_xm / (uniform_sample ** (1 / self.pareto_a))
        
        # Scale the sample to fit within the range [0, M]
        pareto_sample = pareto_sample - self.pareto_xm  # Shift to start from 0
        # Scale the sample to fit within [0, M]
        scaled_sample = pareto_sample * (self.M / (pareto_sample + self.pareto_xm))
    
        # Fit the sample is within the integer range [0, M]
        integer_sample = min(max(int(scaled_sample), 0), self.M)

        return integer_sample

    def samlple_uniform(self):
        """
        Generate samples from a uniform distribution.

        Returns a samples drawn from the uniform distribution [0, self.M].
        """
        # Generate uniform random samples
        sample = np.random.uniform(0, self.M, 1)
        return int(sample)
    
    def sample_normal(self):
        """
        Generate a sample from a normal distribution with arbitrary mean in [0, M].

        Returns:
        - An integer sample drawn from the normal distribution.
        """
        # Generate normal random sample
        sample = np.random.normal(self.M / 2, self.M / 6, 1)
        
        # Ensure the sample is within [0, M]
        sample = np.clip(sample, 0, self.M)
        
        return int(sample)

    def sample_sequential(self, length):
        """
        Generate a sequence of addrs with a given length = frac*M.

        Parameters:
        - length: length of the sequence.

        Returns:
        - samples: a sequence of addrs start from random addr.
        """
        # Generate a sequential trace
        start = np.random.randint(0, self.M - length)
        samples = np.arange(start, start + length)
        return samples

    def generate_zipf_ird_mix(self, k=3, s=2, irm_frac=0, zipf_a=1.2):
        '''
        Generate a synthetic trace;
        irm_frac specifies the fraction of the trace that follows IRM (item drawn from a zipf-like distribution);
        zipf_a defines the zipf-like distribution parameter, only relevant if irm_frac > 0.
        '''
        if k < 3:
            raise ValueError("The number of classes must be greater than 3.")
        elif (k==3):
            self.assign_3_weights(s) 
            self.k=k
        else:
            self.assign_weights_with_k_s(k,s)
            self.k=k
        self.s=s
        self.irm_frac =irm_frac 
        self.zipf_a = zipf_a
        trace, is_irm = gen_from_both(self.sample_ird, self.sample_zipf, self.M, self.n, irm_frac)
        self.trace = trace
        self.is_irm = is_irm
        return trace, is_irm

    
    def generate_trace(self, p_irm, irm_type = None):
        '''
        Generate a synthetic trace;
        p_irm specifies the fraction of the trace that follows IRM (item drawn from a zipf-like distribution);
        irm_type defines the IRM distribution type, only relevant if p_irm > 0.
        '''
        self.p_irm = p_irm
        if irm_type == 'zipf' or irm_type is None:
            trace, is_irm  = gen_from_both(self.sample_ird, self.sample_zipf, self.M, self.n, p_irm)
        elif irm_type == 'pareto':
            trace, is_irm = gen_from_both(self.sample_ird, self.sample_pareto, self.M, self.n, p_irm)
        elif irm_type == 'uniform':
            trace, is_irm = gen_from_both(self.sample_ird, self.samlple_uniform, self.M, self.n, p_irm)
        elif irm_type == 'normal':
            trace, is_irm = gen_from_both(self.sample_ird, self.sample_normal, self.M, self.n, p_irm)
        # elif irm_type == 'sequential': # deal with this later...
        #     if self.seq_length is None:
        #         raise ValueError("Please assign a length to the sequential trace first.")
        #     trace, is_irm = gen_from_ird_seq()
        else:
            raise ValueError("Invalid IRM distribution type.")
        return trace, is_irm