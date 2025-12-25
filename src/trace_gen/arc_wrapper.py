from ctypes import *
import numpy as np
import _arc


class arc:
    def __init__(self, C):
        self.a = _arc.arc_create(C)
        self.C = C

    def run(self, trace):
        if type(trace[0]) != np.int32:
            trace = np.array(trace, dtype=np.int32)
        _arc.arc_run(self.a, len(trace), trace)
        

    def hitrate(self):
        a, m = self.data()
        return 1-(m-self.C)/(a-self.C)

    def data(self) -> tuple: # return (accesses, misses)
        return _arc.arc_data(self.a)
