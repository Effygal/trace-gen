# trace_gen ![MIT](https://img.shields.io/badge/license-MIT-blue.svg) 
**[A library that generates realistic block I/O workloads](https://https://github.com/Effygal/trace-gen)**
## Status

Generates traces of 1D integer array that represent address accesses;

Modules:
    (1) `TraceGenerator`---generate synthetic traces from scratch with specified parameters;
    (2) `TraceReconstructor`---generate synthetic traces that are reconstructed based on a given real-world trace; supports inter-reference distance-based reconstruction and frequency-based reconstruction;
    (3) `LRU` cache simulator (novel); 
    (4) `FIFO` cache simulator;
    (5) `CLOCK` cache simulator.
## Installation
Under the main trace-gen directory, install `trace_gen` via pip:
```bash
pip install .
```
Or install the release/distribute version:
```bash
pip install trace_gen-0.1.0-cp310-cp310-linux_x86_64.whl
```
## Usage

Under any development directory:

```Python
import trace_gen as tg
```

### TraceGenerator
Use TraceGenerator to generate a trace of length $n$, with reference addresses in $\{0 \cdots M-1\}$, with `f`--an probability vector specifying weight of each IRD class, the IRM fraction $p_{irm} \in [0.0, 1.0]$, specifying the fraction of the arrivals following IRM (Zipf, Pareto, Normal, Uniform):
```Python
g1 = tg.TraceGenerator(M = 100, n = 10000)
f1 = tg.fgen(20, [0,3], 5e-3)
trace1 = g1.gen_from_pdf(f1, p_irm=0.2)
```
IRM type use Zipf(1.2) by default; configuring IRM type with:
```
g.set_irm_type('pareto')
g.set_pareto(a, xm)
```

### MRCs under various settings
Use interactive visualization to monitor MRC and fgen, need bokeh installed;
under /interactive directory, run:
```
bokeh serve --show vis_server.py --port <port>
```

#### Vary the IRM fraction $p \in [0, 1]$:
- When $p=0.5$, the trace is 50% freq-based and 50% ird-based, MRC convex/concave behavior shows evenly combined:

- When $p = 1$, the trace is 100% freqency-based, MRC behaves convex.

- When $p=0$, the trace is 100% ird-based, MRC behaves (somewhat) concave:

- When $p=0.2$, the trace is 20% frequency-based and 80% ird-based, MRC behaves somewhat mixed:
etc.

#### vary f

- Adjust slider for the number of IRD classes $k \in \mathbb{Z}_+$;

- Input spike indices I as a list;

- Adjust slider for epsilon

### MRCs of real traces
[See report](figures/real_mrc.pdf)
[See jupyter notebook](traceRecon.ipynb)

### TraceReconstructor
Use `TraceReconstructor` to pull out statistics and reconstruct synthetic traces of given real trace `trc` of length $n$, assume `trc` is block-addressable:
```Python
trc_reconstructor = tg.TraceReconstructor(trc)
```
Inter-reference distance-based reconstruction:
```python
trc_irt_reconstructed = trc_reconstructor.gen_from_ird(n=100000)
```
Frequency-based reconstruction:
```python
trc_irm_reconstructed = trc_reconstructor.gen_from_irm(n=100000)
```
<!-- ### HASH-based sampling
SHARDS item sampling:
- $hash(a)$ mod $P < T$, where $P$ is the modulus (e.g. 100) and $T$ is the threshhold;
- Has a samping rate of $R = T/P$, each sample represents $1/R$ addresses;
- Subset-inclusion;
- each computed stack distance must be scaled by $1/R$;
- SHARDS shows empirical evidencethat $R = 0.001$ (sampled set size $R\cdot M$; sample trace size $R \cdot N$) yields very accurate MRCs;
- Evaluation: use open-source C-implementation of PARDA which takes a trace as input, computes SD offline, yields an MRC; 
- Implementation: 2 data structures:
    - a hash table maps a addr to its most recent refer timestamp;
    - a splay tree to compute num of distinct addrs since this time stamp.
- Minor modify PARDA code:
    - hash each referenced addr, process only when $hash(a) \ mod \ P < T$ is met; $P$ is set to a power of 2 and "mod $P$" is implemented with inexpensive "$\& (P-1)$";
    - For a given sampling rate $R$, set threshhold $T = round(R \cdot P)$;
    - use the public domain C implementation of MurmurHash to achieve hashing;
    - each computed SD is simply divided by $R$ to align with scaled distance $SD/R = (SD \cdot P) / T$.

- PARDA binary trace format: a sequence of 64-bit references, with no additional metadata; need to convert I/O traces to the PARDA format, assume fixed cache block size,  ignore distinction between reads and writes;
- either fixed-sample size ($M$) is suitable for online use in memory-constrained systems such as device deivers in embedded systems; uses automatic rate adaptation to eliminate the need to specify $R$. Starts with $R_0 = 0.1$, and lower progressively as more uunique addrs are encountered;
- or fixed-rate sampling: fix $R$. -->
### Trace simulation tools

Provides relatively high-performance FIFO, LRU and CLOCK simulators.

usage: 
```
        f = tg.fifo(30000)
        f.run(trace)
        f.hitrate()
```

`trace` is a numpy array of integer block addresses, preferably np.int32. (it will be converted to signed 32-bit if not already)

Note that memory usage is dependent on cache size + largest address, so if you have a sparse address range you should use the `misc.squash` function to compact it.

You can run multiple traces on the same fifo/lru/clock object. The command `f.data()` returns the tuple A,M,C:

- A = total number of accesses (so far)
- M = number of misses
- C = access number of most recent access to a non-full cache. (in other words, number of accesses to fill cache)

For clock there is a 4th return value, which is the number of items which were recycled from the end of the queue to the beginning due to the accessed bit being set.

There are some helper functions in `misc.py` - `sim_lru(C,trace,raw=False)`, and equivalently for FIFO and CLOCK. If `raw=False`, it returns adjusted hitrate (i.e. ignoring accesses while the cache was filling, this would cause non-monotone in LRU MRCs), while if `raw=True` it just calculates total hits vs accesses.

#### Simulate LRU & FIFO & CLOCK cache hit rate:
`tg` provides wrapper simulators that can be used as follows: 
```Python
c = np.arange(M//100, M, M//100)
hr_trace1_lru = [tg.sim_lru(_c, trace1) for _c in c]
hr_trace1_fifo = [tg.sim_fifo(_c, trace1) for _c in c]
hr_trace1_clock = [tg.sim_clock(_c, trace1) for _c in c]
```
### iad2.py
Calculate inter-arrival distances

usage:
```
        trace = <something-or-other>
        iad = iad2.iad(trace)
        np.plot(np.sort(iad), np.arange(len(iad))/len(iad))
```

The trace is again a numpy array of integers. Memory usage is proportional to the max address value.

### Dummy synthetic traces

The `misc` module contains the following functions:

- `hc(r,f,M)` - return an address in [0,fM] with probability r, and one in [fM,M] with probability (1-r)
- `t_hc(r,f,M)` - return an interarrival distance for r/f hot/cold traffic, chosen with probability r from the hot distribution and (1-r) from the cold one.
- `gen_from_iad(f,M,n)` - generate a trace of `n` accesses from the interarrival distance function `f()` with memory size `M`.

### Cloudphysics traces, unroll.py

You can get the cloudphysics traces from [https://kzn-swift.massopen.cloud/pjd-public/anonymized106.zip](https://kzn-swift.massopen.cloud/pjd-public/anonymized106.zip)

There are 106 traces, w01 through w106. I've put the translated files in the S3 bucket, as well, named e.g. `w05_vscsi1.vscsitrace.txt`, and put a list of the URLs in the file trace-urls.  (some files are named `...vscsi1...` and some are `...vscsi2...`, for a silly reason.)

The format of the trace files is "op,len,address", where op=R/W, and length and address are in 512-byte sectors, e.g.:
```
W 1 711264
W 1 711265
W 1 1232604094
R 16 95513184
R 16 95513200
R 16 926936192
```

We're only looking at the read operations. The easiest way to load them into python is to grep for records containing 'R', delete the first two characters on each line, then load them as n x 2 numpy arrays. This is time consuming, so I did this once and saved files named `/opt/traces/w01_r.txt`, etc. that can be easily loaded into Python using the `numpy` library:
```python
w01 = np.loadtxt('/opt/traces/w01_r.txt',dtype=np.int32)
w01[:,0] += 7
w01 = tg.squash(tg.unroll(w01//8))
```
Once you have these loaded in Python you need to convert them into a form that the simulators can use. To use 4K pages as the unit you need to divide the addresses and lengths by 8 (not 4096 because the original traces come with 512-byte granularity), then you need to "unroll" the length/address pairs. You can do that in Python, but the `unroll` package does it faster

A simple example to show its operation:
```
>>> import numpy as np 
>>> a = np.array([[2,5],[4,10]])
>>> tg.unroll(a)
array([ 5,  6, 10, 11, 12, 13], dtype=int32)
```

In practice you'll use it like this - note that we're using integer divide (`//`) to divide addresses and lengths by 8. In theory we should be rounding lengths up if they're not a multiple of 8, but there don't seem to be many of these in the read operations. (unlike writes)

```python
trace = np.loadtxt(file_path, dtype=np.int32)
trace[:, 0] += 7
trace = tg.unroll(trace // 8)
```

Finally we may want to subsample a trace by only selecting certain addresses; if we do that, we'll want to reduce the address range (using the `squash` function) so the simulations don't use as much memory.

Here we're selecting only addresses which equal 0 mod 17:

```python
trace = tg.squash(trace[trace%17 == 0])
```

(hmm, maybe I should have stored the expanded arrays, but they're quite big)

### AliCloud trace
Under [pjd-rz:/mnt/sda/alibaba_block_traces_2020](pjd-rz:/mnt/sda/alibaba_block_traces_2020)
The trace is quite long, combines all I/O operations recorded in one month's time frame, across 1000 sampled volumes (hard drives); volume number from 0 to 999.
I splited the trace under each volume (still monstrously long). Addrs are 64-bit integer, offset and LBAs are in byte, therefore unrolling them with:
```python
trace = np.loadtxt(file_path, dtype=np.int64)
trace[:, 0] += 4095
trace = tg.unroll(trace // 4096)
```
Real storage I/O traces typically contain richer information for each reference, including a timestamp, access type (read or write), and a location represented as an offset and length. For the experiments in this paper, we converted I/O block traces to the simpler PARDA format: a sequence of 64-bit references, with no additional metadata; assumed a fixed cache block size (4096 bytes), and ignored the distinction between reads and writes as SHARDS does (this is to assume a unified page cache; we only use reads for the CloudPhysics traces). 


