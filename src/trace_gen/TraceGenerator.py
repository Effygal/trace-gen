"""
Trace Generator
- Generate synthetic traces from a set of parameters;
- Sampling ird from the real trace;
Author: Peter Desnoyers & Yirong Wang
Date: 04/23/2024
"""
import numpy as np
from trace_gen.misc import *
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
        self.zipf_a = 1.2 
        self.ird_k = None # num of classes for IRD
        self.irm_k = None # num of classes for IRM
        self.pareto_a = 2.5
        self.pareto_xm = 1 
        self.normal_mean = self.M / 2 
        self.normal_std = self.M / 6 
        self.uniform_a = 0 
        self.uniform_b = self.M-1
        # self.ird_samples = []
        self.p_single = 0.0
        self.ird_sample_mean = None
        self.pdf_b = fgen(20, np.array([0,3]), 0.005)
        self.pdf_c = fgen(20, np.array([2,9]), 0.005) 
        self.pdf_d = fgen(5, np.array([0,4]), 1e-2)
        self.pdf_e = fgen(20, np.array([1]), 5e-3)
        self.pdf_f = fgen(5, np.array([2]), 1e-2)  
        self.irm_type = 'zipf'

    def ird_mean(self): 
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
    
    def set_zipf(self, a):
        self.zipf_a = a
    
    def set_pareto(self, a, xm):
        self.pareto_a = a
        self.pareto_xm = xm
    
    def set_normal(self, mean, std):
        self.normal_mean = mean
        self.normal_std = std

    def set_uniform(self, a, b):
        self.uniform_a = a
        self.uniform_b = b

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
    
    def set_p_single(self, p_single):
        self.p_single = p_single
    
    def sample_zipf(self):
        '''
        Sample an address from a set of different uniform distributions with weights following an inverse power Zipf-like distribution.
        '''
        if self.irm_k is None:
            self.irm_k = len(self.pdf)
        
        num_intervals = self.irm_k
        interval_width = self.M // num_intervals
        
        # Calculate Zipf p
        p = 1.0 / np.power(np.arange(1, num_intervals + 1), self.zipf_a)
        p /= np.sum(p)  # Normalize to sum to 1
        
        # Select an interval based on Zipf p
        choice_interval = np.random.choice(num_intervals, p=p)
        
        # bounds of the chosen interval
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width
        
        # Sample uniformly within the chosen interval
        sample = np.random.uniform(lower_bound, upper_bound)
        
        return sample

    def sample_pareto(self):
        '''
        Sample an address from a set of different uniform distributions with weights following a Pareto distribution.
        '''
        if self.irm_k is None:
            self.irm_k = len(self.pdf)
        
        num_intervals = self.irm_k
        interval_width = self.M // num_intervals
        
        # Calculate Pareto p
        p = (self.pareto_xm / np.arange(1, num_intervals + 1)) ** self.pareto_alpha
        p /= np.sum(p)  # Normalize to sum to 1
        
        # Select an interval based on Pareto p
        choice_interval = np.random.choice(num_intervals, p=p)
        
        # bounds of the chosen interval
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width
        
        # Sample uniformly within the chosen interval
        sample = np.random.uniform(lower_bound, upper_bound)
        
        return sample

    def samlple_uniform(self):
        """
        Generate samples from a uniform distribution.

        Returns a samples drawn from the uniform distribution [0, self.M].
        """
        sample = np.random.uniform(0, self.M, 1)
        return int(sample)
    
    def sample_normal(self):
        """
        Generate a sample from a normal distribution with arbitrary mean in [mean, std].

        Returns:
        - An integer sample drawn from the normal distribution.
        """
        sample = np.random.normal(self.normal_mean, self.normal_std, 1)

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

    def compute_tmax_and_bins(self):
        """
        Compute the value of Tmax and the sample space bins such that the mean of samples drawn is self.M.
        """
        n = len(self.pdf)
        weighted_sum = sum((i + 0.5) * self.pdf[i] for i in range(n))

        # Calculate Tmax s.t. the mean of irds is M
        tmax = (self.M * n) / weighted_sum

        # bin midpoints
        bin_width = tmax / n
        bin_edges = np.array([i * bin_width for i in range(n + 1)])
        self.bin_edges = bin_edges
        self.tmax = tmax
        # return T, bins

    def sample_from_pdf(self):
        if random.random() < self.p_single:
            sample = -1
        else:
            chosen_bin = np.random.choice(len(self.bin_edges)-1, p=self.pdf)
            bin_start = self.bin_edges[chosen_bin]
            bin_end = self.bin_edges[chosen_bin + 1]
            sample = np.random.uniform(bin_start, bin_end)
        # self.ird_samples.append(sample)
        return sample 

    def sample_from_irds(self):
        return np.random.choice(self.irds)

    def gen_from_pdf(self, pdf, p_irm):
        pdf = np.array(pdf)
        pdf /= pdf.sum()
        self.pdf = pdf
        self.p_irm = p_irm
        self.compute_tmax_and_bins()
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

    def gen_from_irds(self, irds, p_single):
        # treat p_single as p_irm
        irds = irds[irds > -1]
        self.irds = irds
        trace, is_irm = gen_from_both(self.sample_from_irds, self.sample_zipf, self.M, self.n, p_single)
        return trace, is_irm