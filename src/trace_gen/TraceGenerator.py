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
import scipy.interpolate as interpolate
    
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
        self.ird_k = None # num of classes for IRD
        self.ird_s = 4 # skewness of the IRD weights
        self.irm_k = None # num of classes for IRM
        self.pareto_a = 2.5 # the shape paremeter of pareto_alpha
        self.pareto_xm = 1 # the scale parameter pareto_xm
        self.ird_samples = []
        self.ird_sample_mean = None
        self.pdf15 = [0.014332888772033765,
                    0.7711220054386558,
                    0.031611140672482836,
                    1.983890796084442e-09,
                    0.001372776398541284,
                    0.12649811391472693,
                    0.00016647713740345087,
                    0.028850763840288743,
                    0.025811135272233738,
                    2.985032662827537e-07,
                    2.966863554549485e-07,
                    0.0002207139479488885,
                    6.681772272474121e-06,
                    6.6781736730528705e-06,
                    2.7486226354857132e-08]
        
        self.irm_type = 'zipf'

    def calculate_ird_mean(self): 
        '''
        - Need to adjust M to mean/10 to scale fit to the same IRD sample space.
        '''
        if self.ird_k is None:
            self.ird_k = len(self.weights)
        segment_length = self.n // self.ird_k
        means = 0
        for i in range(self.ird_k):
            start = i * segment_length
            if i == self.ird_k - 1:
                end = self.n + 1 
            else:
                end = (i + 1) * segment_length
            means += np.mean(np.arange(start, end)) * self.weights[i]
        self.ird_sample_mean = means
        return means
    
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

    def set_irm_type(self, irm_type):
        self.irm_type = irm_type

    def set_ird_pdf(self, pdf):
        self.ird_pdf = pdf
    
    def set_irds(self, irds):
        self.irds = irds

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
        self.ird_k = len(weights)
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
    
    def sample_zipf(self):
        '''
        Sample an address from a set of different uniform distributions with weights following an inverse power Zipf-like distribution.
        '''
        if self.irm_k is None:
            self.irm_k = len(self.weights)
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
    
    # def gen_trace(self, p_irm, irm_type = None):
    #     '''
    #     Generate a synthetic trace;
    #     p_irm specifies the fraction of the trace that follows IRM (item drawn from a zipf-like distribution);
    #     irm_type defines the IRM distribution type, only relevant if p_irm > 0.
    #     '''
    #     self.p_irm = p_irm
    #     self.irm_type = irm_type
    #     if irm_type == 'zipf' or irm_type is None:
    #         trace, is_irm  = gen_from_both(self.sample_from_pdf, self.sample_zipf, self.M, self.n, p_irm)
    #     elif irm_type == 'pareto':
    #         trace, is_irm = gen_from_both(self.sample_from_pdf, self.sample_pareto, self.M, self.n, p_irm)
    #     elif irm_type == 'uniform':
    #         trace, is_irm = gen_from_both(self.sample_from_pdf, self.samlple_uniform, self.M, self.n, p_irm)
    #     elif irm_type == 'normal':
    #         trace, is_irm = gen_from_both(self.sample_from_pdf, self.sample_normal, self.M, self.n, p_irm)
    #     # elif irm_type == 'sequential': # deal with this later...
    #     #     if self.seq_length is None:
    #     #         raise ValueError("Please assign a length to the sequential trace first.")
    #     #     trace, is_irm = gen_from_ird_seq()
    #     else:
    #         raise ValueError("Invalid IRM distribution type.")
    #     return trace, is_irm

    def sample_from_weights(self):
        '''
        Sample ird from the set of different uniform distributions with rates = weights.
        '''
        num_intervals = len(self.weights)
        interval_width = self.M // num_intervals

        # choose from an interval
        choice_interval = np.random.choice(num_intervals, p=self.weights) 

        # calculate the lower and upper bounds of the chosen interval
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width

        # uniformly sample from the chosen interval
        sample = int(np.random.uniform(lower_bound, upper_bound))
        if sample == 0:
            sample = 1
        return sample

    def compute_T_and_bins(self):
        """
        Compute the value of T and the sample space bins such that the mean of samples drawn is self.M.
        """
        n = len(self.pdf)
        
        # Compute the sum of the indices weighted by the pdf
        weighted_sum = sum((i + 0.5) * self.pdf[i] for i in range(n))

        # Calculate T such that the mean matches desired_mean
        T = (self.M * n) / weighted_sum

        # Calculate bin midpoints
        bin_width = T / n
        bin_edges = np.array([i * bin_width for i in range(n + 1)])
        self.bin_edges = bin_edges
        self.T = T
        # return T, bins

    def sample_from_pdf(self):
        chosen_bin = np.random.choice(len(self.bin_edges)-1, p=self.pdf)
        bin_start = self.bin_edges[chosen_bin]
        bin_end = self.bin_edges[chosen_bin + 1]
        sample = np.random.uniform(bin_start, bin_end)
        self.ird_samples.append(sample)
        return sample 

    def sample_from_irds(self):
        return np.random.choice(self.irds)

    def gen_from_pdf(self, pdf, p_irm):
        pdf = np.array(pdf)
        pdf /= pdf.sum()
        self.pdf = pdf
        self.p_irm = p_irm
        self.compute_T_and_bins()
        if self.irm_type == 'zipf' or self.irm_type is None:
            trace, is_irm, tv  = gen_from_both(self.sample_from_pdf, self.sample_zipf, self.M, self.n, p_irm)
        elif self.irm_type == 'pareto':
            trace, is_irm, tv = gen_from_both(self.sample_from_pdf, self.sample_pareto, self.M, self.n, p_irm)
        elif self.irm_type == 'uniform':
            trace, is_irm, tv = gen_from_both(self.sample_from_pdf, self.samlple_uniform, self.M, self.n, p_irm)
        elif self.irm_type == 'normal':
            trace, is_irm, tv = gen_from_both(self.sample_from_pdf, self.sample_normal, self.M, self.n, p_irm)
        # elif irm_type == 'sequential': # deal with this later...
        #     if self.seq_length is None:
        #         raise ValueError("Please assign a length to the sequential trace first.")
        #     trace, is_irm = gen_from_ird_seq()
        else:
            raise ValueError("Invalid IRM distribution type.")
        return trace, is_irm, tv
     
    def gen_from_weights(self, weights, p_irm):
        self.weights = weights
        self.weights = np.array(self.weights)
        self.weights /= self.weights.sum() 
        trace, is_irm  = gen_from_both(self.sample_from_weights, self.sample_zipf, self.M, self.n, p_irm)
        return trace, is_irm

    def gen_from_irds(self, irds, p_single):
        # treat p_single as p_irm
        irds = irds[irds > -1]
        self.irds = irds
        trace, is_irm = gen_from_both(self.sample_from_irds, self.sample_zipf, self.M, self.n, p_single)
        return trace, is_irm