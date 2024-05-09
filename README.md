# trace_gen ![MIT](https://img.shields.io/badge/license-MIT-blue.svg) 
**[A prototype library that generates realistic block IO workloads](https://https://github.com/Effygal/zns-obj)**
## Status

Generates traces of 1D integer array that represent read address accesses;

Modules:
    (1) `TraceGenerator`---generate a synthetic trace with a list of Poisson rates that add up to one as input.
    (2) `TraceReconstructor`---generate synthetic traces with a real-world trace as input. Supports inter-reference time-based reconstruction and frequency-based reconstruction.
    (3) `LRU` cache simulator. 
## Installation
Under the main trace-gen directory, install `trace_gen` via pip:
```bash
pip install .
```
Or install the compressed release version:
```bash
pip install trace_gen-0.1.0-cp310-cp310-linux_x86_64.whl
```
## Usage

Under any development directory:

```Python
import trace_gen as tg
```

### TraceGenerator
Use TraceGenerator to generate a trace of length $n$, with accesses in $\{0 \cdots M-1\}$, with $k$ uniform inter-reference distance (IRD) classes, and with skewness $s$ (optional):
```Python
generator = tg.TraceGenerator(M = 1000, N = 10000)
trace1 = generator.generate_trace(k = 5, s = 2)
```
Simulate LRU & FIFO cache hit rate:
```Python
c = np.arange(M//100, M, M//100)
hr_trace1_lru = [tg.sim_lru(_c, trace1) for _c in c]
hr_trace1_fifo = [tg.sim_fifo(_c, trace1) for _c in c]
```

#### Stratified uniform IRD distriutions
- Stratification by specifying number of IRD classes and skewness (optional).

- MRCs and corresponding IRD distribution under different settings:
![](figures/class10.png)
<!-- ![](figures/class10_2.png) -->
![](figures/class5.png)
![](figures/class4.png)

- MRCs and corresponding IRD distribution under different settings (with skewness specification):
![](figures/class10skew2.png)
![](figures/class5skew3.png)
![](figures/class5skew2.png)
![](figures/class5skew1.png)
![](figures/class4skew3.png)
![](figures/class4skew2.png)
![](figures/class4skew1.png)


### TraceReconstructor
Use `TraceReconstructor` to reconstruct a synthetic trace of given real trace `w26` of length $n$:
```Python
w26 = np.loadtxt(f'/opt/traces/w26_r.txt', dtype=np.int32)
w26_reconstructor = tg.TraceReconstructor(w26)
```
Inter-reference time-based reconstruction:
```Python
w26_irt_reconstructed = w26_reconstructor.generate_irt_trace(n=100000)
```
Frequency-based reconstruction:
```Python
w26_irm_reconstructed = w26_reconstructor.generate_irm_trace(n=100000)
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




