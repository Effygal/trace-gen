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
Use TraceGenerator to generate a trace of length $n$, with accesses in $\{0 \cdots M-1\}$, with three uniform irt classes with selection probabilities $\{0.1, 0.3, 0.6\}$:
```Python
generator1 = tg.TraceGenerator(M = 1000, N = 10000, w_r_ratio = 0.5, params = np.array([0.1, 0.3, 0.6]))
trace1 = generator1.generate_trace()
```
Simulate LRU cache hit rate:
```Python
c = np.arange(1000, 100000, 3000)
hr_trace1 = [tg.sim_lru(_c, trace1) for _c in c]
```

#### Stratified uniform irt distriutions
- Stratification by uniform params in monotonically increasing order (e.g. $\{0.1, 0.3, 0.6\}$) generates concave MRCs;

The result MRC and corresponding irt distribution:
<div style="display: flex;">
    <div style="flex: 50%; padding: 5px;">
        <p>Hit ratio curve for trace1 under LRU</p>
        <img src="figures/uniform11.png" alt="Hit ratio curve" style="width: 100%;">
    </div>
    <div style="flex: 50%; padding: 5px;">
        <p>IRT distribution for trace1</p>
        <img src="figures/uniform12.png" alt="IRT distribution" style="width: 100%;">
    </div>
</div>

- Stratification by uniform params in non-increasing or arbitrary order (e.g. $\{0.6, 0.3, 0.1\}$ or $\{0.6, 0.1, 0.3\}$) generates "ugly" MRCs;
```Python
generator2 = tg.TraceGenerator(1000, 10000, 0.5, np.array([0.6, 0.3, 0.1]))
trace2 = generator2.generate_trace()
```
```Python
hr_trace2 = [tg.sim_lru(_c, trace2) for _c in c]
```
<div style="display: flex;">
    <div style="flex: 50%; padding: 5px;">
        <p>Hit ratio curve for trace1 under LRU</p>
        <img src="figures/uniform21.png" alt="Hit ratio curve" style="width: 100%;">
    </div>
    <div style="flex: 50%; padding: 5px;">
        <p>IRT distribution for trace1</p>
        <img src="figures/uniform22.png" alt="IRT distribution" style="width: 100%;">
    </div>
</div>

```Python
generator3 = tg.TraceGenerator(1000, 10000, 0.5, np.array([0.6, 0.1, 0.3]))
trace3 = generator3.generate_trace()
```
```Python
hr_trace3 = [tg.sim_lru(_c, trace3) for _c in c]
```
<div style="display: flex;">
    <div style="flex: 50%; padding: 5px;">
        <p>Hit ratio curve for trace1 under LRU</p>
        <img src="figures/uniform31.png" alt="Hit ratio curve" style="width: 100%;">
    </div>
    <div style="flex: 50%; padding: 5px;">
        <p>IRT distribution for trace1</p>
        <img src="figures/uniform32.png" alt="IRT distribution" style="width: 100%;">
    </div>
</div>

```Python
generator4 = tg.TraceGenerator(1000, 10000, 0.5, np.array([0.4, 0.15, 0.25, 0.2]))
trace4 = generator4.generate_trace()
```
```Python
hr_trace4 = [tg.sim_lru(_c, trace4) for _c in c]
```
<div style="display: flex;">
    <div style="flex: 50%; padding: 5px;">
        <p>Hit ratio curve for trace1 under LRU</p>
        <img src="figures/uniform41.png" alt="Hit ratio curve" style="width: 100%;">
    </div>
    <div style="flex: 50%; padding: 5px;">
        <p>IRT distribution for trace1</p>
        <img src="figures/uniform42.png" alt="IRT distribution" style="width: 100%;">
    </div>
</div>

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




