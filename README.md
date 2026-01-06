# 2DIO trace-gen ![MIT](https://img.shields.io/badge/license-MIT-blue.svg) 
**[A cache-accurate synthetic I/O generator](https://https://github.com/Effygal/trace-gen)**

## Build prerequisites 

### System dependencies:
- Linux (tested on Ubuntu 24.04.2 LTS)
- Meson build system (tested on meson 1.9.0)
- C++ compiler (tested on gcc 13.3.0)
- Boost >= 1.83.0
- Python 3.10+
- pip and build tools
- Bokeh (tested on 3.8.0)

For Debian-based distros, you can install these directly with `apt-get`:
```bash
sudo apt-get install build-essential libboost-all-dev libfmt-dev pkg-config
```

### Install
If you are on Linux x86, you can install the package directly from the wheel (see GH releases): 
```bash
python -m pip install trace_gen-0.2.1-cp310-cp310-linux_x86_64.whl
```
If you prefer building from the source:
```bash
python -m build
```
<!-- You can build a wheel file:
```bash
python -m build --wheel
``` -->
Under the main trace-gen directory, install via pip:
```bash
python -m pip install .
```
Verify the CLI tool:
```bash
trace-gen --help
```
then verify the Python lib:
```bash
pip show trace_gen
```

## Contents

### 1. Standalone CLI `trace-gen`

```
Allowed options:
  -h [ --help ]                   Produce this message
  -m [ --addresses ] arg          Footprint size (number of unique addresses)
  -n [ --length ] arg             Length of trace (in addresses)
  -p [ --p_irm ] arg              Probability of the trace that is IRM (float
                                  between 0 and 1)
  -s [ --seed ] arg (=42)         RNG seed
  -b [ --blocksize ] arg (=4096)  Size of a block in bytes
  -f [ --ird ] arg (=b)           IRD distribution. Can be one of the
                                  pre-specified distributions (b to f) or
                                  inputs to fgen (k # of classes, non-spike
                                  heights, and indices of spikes) separated by
                                  columns. Example: -f b or -f
                                  fgen:10000:0.00001:3,5,10,20
  -g [ --irm ] arg (=zipf:1.2,20) IRM distribution. Can be: zipf:alpha,n,
                                  pareto:xm,a,n, uniform:max,
                                  normal:mean,stddev.
  -r [ --rwratio ] arg (=1)       Fraction of addresses that are reads (vs
                                  writes)
  -z [ --sizedist ] arg (=1:1)    Distribution of request sizes in
                                  blocks.Specified as a list of weights
                                  (floats) followed by a list of sizes in
                                  blocks (ints).Ex: 1,1,1:1,3,4 means equal
                                  chance of 1, 3, or 4-block requests
```

Examples:

```
# 100 address footprint, 10k trace length, 50% IRM, type 'c' IRD, 4k block size, 
trace-gen -m 100 -n 10000 -p 0.5 -f c -b 4096

# 50% reads, 50% writes, sizes are evenly distributed between 1 and 2 blocks
trace-gen -m 100 -n 10000 -p 0.5 -f c -r 0.5 -z 1,1:1,2

# seed rng with 42
trace-gen -m 100 -n 10000 -p 0.5 -f c -r 0.5 -z 1,1:1,2 -s 42

# make the trace all reads instead (default behaviour)
trace-gen -m 100 -n 10000 -p 0.5 -f c -z 1,1:1,2 -s 42

# have a 25/25/50 split of 1, 3, and 4 block requests
trace-gen -m 100 -n 10000 -p 0.5 -f c -z 1,1,2:1,3,4 -s 42

# set blocksize to one (so generated addresses are adjacent)
trace-gen -m 100 -n 10000 -p 0.5 -f c -z 1,1,2:1,3,4 -s 42 -b 1

# use fgen to specify a custom IRD distribution with 15 classes, spikes at indices 1, 3, 5, 9 and epsilon=0.01; 10% accesses are IRM, which follow Pareto distribution with xm=1, a=2.5, discretized into 100 classes.
trace-gen -m 10000 -n 1000000 \
    -f fgen:15:0.01:1,3,5,9 \
    -g pareto:1,2.5,100 \
    -p 0.1
```
Output traces are in SPC format.

### 2. Python lib 

```Python
import trace_gen as tg
```

#### TraceGenerator
```Python
g = tg.TraceGenerator(m=100, n=10000)              # 100 addrs, length 10k
f1 = tg.fgen(20, [0,3], 5e-3)                      # 20 IRD classes, spikes at 0 & 3, ε=5e-3
trace1 = g.gen_from_pdf(f1, p_irm=0.2)             # 20% arrivals follow IRM
```

Configuring IRM type with, default to Zipf(1.2):
```
g.set_irm_type('pareto')
g.set_pareto(a, xm)
```

### 3. Interactive parameter-searching
- under /interactive directory, run:
```bash
bokeh serve --show vis_server.py --port <port>
```
- Monitor how the HRC changes as you tweak parameters; once you reach the target curve, copy those settings into the CLI or Python API to generate traces. (Scaling m and n doesn’t affect the shape.)

<!-- ### TraceReconstructor
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
``` -->
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

### 4. Trace processors

#### Cloudphysics traces, unroll.py

You can get the cloudphysics traces from [https://kzn-swift.massopen.cloud/pjd-public/anonymized106.zip](https://kzn-swift.massopen.cloud/pjd-public/anonymized106.zip)
[pjd-rz:/mnt/sda/anonymized106](pjd-rz:/mnt/sda/anonymized106)

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
The easiest way to load them into python is to delete the first two characters on each line, then load them as n x 2 numpy arrays. 
In practice you'll use it like this - note that we're using integer divide (`//`) to divide addresses and lengths by 8. In theory we should be rounding lengths up if they're not a multiple of 8, but there don't seem to be many of these in the read operations. (unlike writes).
```python
w01 = np.loadtxt(file_path, dtype=np.int32)
w01[:,0] += 7
```
Once you have these loaded in Python you need to convert them into a form that the simulators can use. To use 4K pages as the unit you need to divide the addresses and lengths by 8 (not 4096 because the CloudPhysics traces come with 512-byte granularity).

Then you need to "unroll" the length/address pairs. You can do that in Python, but the `unroll` package does it faster
```Python
w01 = tg.squash(tg.unroll(w01//8))
```

A simple example to show its operation:
```Python
>>> import numpy as np 
>>> a = np.array([[2,5],[4,10]])
>>> tg.unroll(a)
array([ 5,  6, 10, 11, 12, 13], dtype=int32)
```

#### AliCloud trace
Available at: https://github.com/alibaba/block-traces.
The trace is quite long, combines all I/O operations recorded in one month's time frame, across 1000 sampled volumes (hard drives); volume number from 0 to 999.
Addrs are 64-bit integer, offset and LBAs are both in byte, therefore you should unroll them with:
```Python
volume01 = np.loadtxt(file_path, dtype=np.int64)
volume01[:, 0] += 4095
volume01 = tg.unroll(volume01 // 4096)
```
`volume01` is a now numpy array of integer block addresses, preferably np.int32. (it will be converted to signed 32-bit if not already)

#### Subsampling traces
Finally we may want to subsample a trace by only selecting certain addresses; if we do that, we'll want to reduce the address range (using the `squash` function) so the simulations don't use as much memory.

Here we're selecting only addresses which equal 0 mod 17:
```Python
volume01 = tg.squash(volume01[volume01%17 == 0])
```

### 5. Cache simulators and others
We ship several cache simulators; all expose `.run(trace)` and `.hitrate()` plus `data()` for raw counters.

- **LRU / FIFO / LFU**: Simple policies via `tg.lru`, `tg.fifo`, `tg.lfu`.
- **CLOCK(K)**: CLOCK with configurable counter cap `K`. (`K=1` reduces to the classic CLOCK [1]; `K=0` reduces the algorithm to FIFO).
- **RanCLOCK(K)**: CLOCK with randomized hand; same `K` semantics. (`K=0` reduces to RANDOM).
- **SIEVE(K)**: a variant of [2] with counter cap `K`. (`K=1` reduces to the original SIEVE [2]; similarly, `K=0` reduces to FIFO).
- **RanSIEVE(K)**: Randomized SIEVE variant. Algorithmaically identical to RanCLOCK. (But we needed to test if it's true.)(again, `K=0` reduces to RANDOM).
- **FIFO(m) and RAND(m)**: Multi-queue/list-based policies [3]; lists are configured as `[m1, m2, …]` using parameters `m1` (first-list size as a fraction of total cache `C`) and `h` (number of lists).
- **MIN**: Belady's oracle.

Example:
```python
f = tg.fifo(30000)
f.run(volume01)
f.hitrate()

rc = tg.ranclock(50000, K=15)
rc.run(volume01)
rc.hitrate()
```

Note that memory usage is dependent on cache size + largest address, so if you have a sparse address range you should use the `misc.squash` function to compact it.

You can run multiple traces on the same object;`f.data()` returns the tuple A,M,C:

- A = total number of accesses (so far)
- M = number of misses
- C = access number of most recent access to a non-full cache. (in other words, number of accesses to fill cache)

For CLOCK/RanCLOCK there is a 4th return value, which is the number of items which were recycled from the end of the queue to the beginning due to the accessed counter being set.

There are some helper functions in `misc.py` - `sim_lru(C,trace,raw=False)`, and equivalently for FIFO and CLOCK. If `raw=False`, it returns adjusted hitrate (i.e. ignoring accesses while the cache was filling), while if `raw=True` it just calculates total hits vs accesses.

#### Simulate cache hit rate:
`tg` provides wrapper simulators that can be used as follows: 
```Python
c = np.arange(m//100, m, m//100)
hr_volume01_lru = [tg.sim_lru(_c, volume01) for _c in c]
hr_volume01_fifo = [tg.sim_fifo(_c, volume01) for _c in c]
hr_volume01_clock = [tg.sim_clock(_c, volume01) for _c in c]
```

#### iad2.py
Calculate the inter-reference distances of a given trace
usage:
```Python
iad = iad2.iad(volume01)
np.plot(np.sort(iad), np.arange(len(iad))/len(iad))
```


[1]: F. J. Corbató et al., “The Multics System: An Examination of its Structure,” 1969 — introduces second-chance/CLOCK paging.

[2]: Y. Zhang, J. Yang, Y. Yue, Y. Vigfusson, K. V. Rashmi, “SIEVE is simpler than LRU: an efficient Turn-Key eviction algorithm for web caches,” USENIX NSDI 2024.

[3]: N. Gast and B. Van Houdt, “Transient and steady-state regime of a family of list-based cache replacement algorithms,” ACM SIGMETRICS 2015.
