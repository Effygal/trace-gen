import numpy as np
from trace_gen.misc import *
import random
# import scipy.interpolate as interpolate
import bisect

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
        if self.irm_k is None:
            self.irm_k = len(self.pdf)
        
        num_intervals = self.irm_k
        interval_width = self.M // num_intervals
        
        p = 1.0 / np.power(np.arange(1, num_intervals + 1), self.zipf_a)
        p /= np.sum(p) 
        
        choice_interval = np.random.choice(num_intervals, p=p)
        
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width
        
        sample = np.random.uniform(lower_bound, upper_bound)
        
        return sample

    def sample_pareto(self):
        if self.irm_k is None:
            self.irm_k = len(self.pdf)
        
        num_intervals = self.irm_k
        interval_width = self.M // num_intervals
        
        p = (self.pareto_xm / np.arange(1, num_intervals + 1)) ** self.pareto_alpha
        p /= np.sum(p)  
        
        choice_interval = np.random.choice(num_intervals, p=p)
        
        lower_bound = choice_interval * interval_width
        upper_bound = (choice_interval + 1) * interval_width
        
        sample = np.random.uniform(lower_bound, upper_bound)
        
        return sample

    def samlple_uniform(self):
        sample = np.random.uniform(0, self.M, 1)
        return int(sample)
    
    def sample_normal(self):
        sample = np.random.normal(self.normal_mean, self.normal_std, 1)

        sample = np.clip(sample, 0, self.M)
        
        return int(sample)

    def sample_sequential(self, length):
        start = np.random.randint(0, self.M - length)
        samples = np.arange(start, start + length)
        return samples

    def compute_tmax_and_bins(self):
        n = len(self.pdf)
        weighted_sum = sum((i + 0.5) * self.pdf[i] for i in range(n))

        # Calculate Tmax s.t. the mean of irds is M
        tmax = (self.M * n) / weighted_sum

        bin_width = tmax / n
        bin_edges = np.array([i * bin_width for i in range(n + 1)])
        self.bin_edges = bin_edges
        self.tmax = tmax
        # return T, bins

    # def sample_from_pdf(self): #takes O(k) time
    #     if random.random() < self.p_single:
    #         sample = -1
    #     else:
    #         chosen_bin = np.random.choice(len(self.bin_edges)-1, p=self.pdf)
    #         bin_start = self.bin_edges[chosen_bin]
    #         bin_end = self.bin_edges[chosen_bin + 1]
    #         sample = np.random.uniform(bin_start, bin_end)
    #     # self.ird_samples.append(sample)
    #     return sample 

    def sample_from_pdf(self):
        if random.random() < self.p_single:
            sample = -1
        else:
            u = random.random()
            chosen_bin = bisect.bisect_right(self.cdf, u)
            bin_start = self.bin_edges[chosen_bin]
            bin_end = self.bin_edges[chosen_bin + 1]
            sample = np.random.uniform(bin_start, bin_end)
        return sample

    def sample_from_irds(self):
        return np.random.choice(self.irds)

    def gen_from_pdf(self, pdf, p_irm): 
        pdf = np.array(pdf)
        pdf /= pdf.sum()
        self.pdf = pdf
        self.cdf = np.cumsum(self.pdf)
        self.cdf[-1] = 1.0
        self.p_irm = p_irm
        self.compute_tmax_and_bins()
        if self.irm_type == 'zipf' or self.irm_type is None:
            trace = gen_from_both(self.sample_from_pdf, self.sample_zipf, self.M, self.n, p_irm)
        elif self.irm_type == 'pareto':
            trace = gen_from_both(self.sample_from_pdf, self.sample_pareto, self.M, self.n, p_irm)
        elif self.irm_type == 'uniform':
            trace = gen_from_both(self.sample_from_pdf, self.samlple_uniform, self.M, self.n, p_irm)
        elif self.irm_type == 'normal':
            trace = gen_from_both(self.sample_from_pdf, self.sample_normal, self.M, self.n, p_irm)
        # elif irm_type == 'sequential': # deal with this later...
        #     if self.seq_length is None:
        #         raise ValueError("Please assign a length to the sequential trace first.")
        #     trace, is_irm = gen_from_ird_seq()
        else:
            raise ValueError("Invalid IRM distribution type.")
        return trace

    def gen_from_irds(self, irds, p_single):
        # treat p_single as p_irm
        irds = irds[irds > -1]
        self.irds = irds
        trace = gen_from_both(self.sample_from_irds, self.sample_zipf, self.M, self.n, p_single)
        return trace