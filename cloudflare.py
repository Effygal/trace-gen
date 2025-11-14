# %%
from __future__ import annotations
import csv
import io
from collections import Counter
from pathlib import Path
from typing import Iterable, Iterator
import numpy as np
import zstandard as zstd
import numpy as np
import trace_gen as tg
import matplotlib.pyplot as plt
from scipy import stats
import seaborn as sns
import pandas as pd
from scipy import stats
import matplotlib.ticker as ticker
import scipy.stats as ss
plt.rcParams['pdf.fonttype'] = 42 
plt.rcParams['ps.fonttype'] = 42 
plt.rcParams['image.cmap'] = 'viridis'
plt.rcParams['text.usetex']  = False
# Set the seaborn default color palette
colors = sns.color_palette("deep")
import trace_gen as tg
import matplotlib.ticker as ticker

def row_iter(trace_path: Path) -> Iterator[dict[str, str]]:
    with trace_path.open("rb") as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            text_stream = io.TextIOWrapper(reader, encoding="utf-8", newline="")
            try:
                csv_reader = csv.DictReader(text_stream)
                for row in csv_reader:
                    yield row
            finally:
                text_stream.detach()

def count_keys(rows: Iterable[dict[str, str]], sample: int | None = None) -> Counter[str]:
    counter: Counter[str] = Counter()
    for index, row in enumerate(rows):
        key = row.get("key")
        if key:
            counter[key] += 1
        if sample is not None and index + 1 >= sample:
            break
    return counter

def load_key_counter(trace_path: Path, sample: int | None = None) -> Counter[str]:
    rows = row_iter(trace_path)
    return count_keys(rows, sample=sample)

def load_key_and_ttl(trace_path: Path, sample: int | None = None, start: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    if start is not None and start < 0:
        raise ValueError("`start` must be non-negative.")
    if sample is not None and sample <= 0:
        return np.array([], dtype=np.uint64), np.array([], dtype=np.int64)

    keys: list[int] = []
    ttls: list[int] = []
    skipped = 0
    start_index = start or 0

    for row in row_iter(trace_path):
        raw_key = row.get("key")
        expiry_time = row.get("expiry_time")
        if raw_key is None or expiry_time is None:
            continue
        try:
            key_value = int(raw_key, 16)
            ttl_value = int(expiry_time)
        except ValueError:
            continue

        if skipped < start_index:
            skipped += 1
            continue

        keys.append(key_value)
        ttls.append(ttl_value)

        if sample is not None and len(keys) >= sample:
            break

    return np.array(keys, dtype=np.uint64), np.array(ttls, dtype=np.int64)

def proc_trc(file_name):
    path = Path('/mnt/sda/cloudflare') / (file_name + '.csv.zst')
    keys, ttls = load_key_and_ttl(path, sample=10000000)
    _, keys = np.unique(keys, return_inverse=True)
    keys = keys.astype(np.int32, copy=False)
    iads = tg.iad(keys)
    return ttls, keys, iads

from matplotlib.ticker import ScalarFormatter, LogFormatterSciNotation, LogLocator

def _fmt_axis(ax, use_log_y):
    xfmt = ScalarFormatter(useMathText=True)
    xfmt.set_powerlimits((-3, 3))
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis.get_offset_text().set_fontsize(16)

    if use_log_y:
        yfmt = LogFormatterSciNotation()
        yfmt.labelOnlyBase = False
        ax.yaxis.set_major_formatter(yfmt)
    else:
        yfmt = ScalarFormatter(useMathText=True)
        yfmt.set_powerlimits((-3, 3))
        ax.yaxis.set_major_formatter(yfmt)
    ax.yaxis.get_offset_text().set_fontsize(16)

    ax.tick_params(axis='both', which='major', labelsize=16)

def plot_irds(file_name, iads, bins=50):
    palette = colors
    total = iads.size
    positive = iads[iads > 0]

    fig, ax = plt.subplots(figsize=(6, 4.5))

    positive_min, positive_max = 1e-3, 1.0
    ymin = 1e-12

    if positive.size:
        bin_edges = np.histogram_bin_edges(positive, bins=bins)
        counts, _ = np.histogram(positive, bins=bin_edges)
        widths = np.diff(bin_edges)
        densities = counts / (total * widths)
        mask = densities > 0

        ax.bar(
            bin_edges[:-1][mask],
            densities[mask],
            width=widths[mask],
            align='edge',
            color=palette[0],
            alpha=0.65,
            edgecolor='white',
        )

        positive_min, positive_max = positive.min(), positive.max()

    ax.set_xlabel('Inter-arrival Distance', fontsize=22)
    ax.set_ylabel('PMF', fontsize=22)
    ax.set_yscale('log')
    _fmt_axis(ax, use_log_y=True)

    ymin, ymax = ax.get_ylim()
    ymin = max(ymin, 1e-12)

    infinite_mask = iads == -1
    infinite_bar_top = None
    if infinite_mask.any():
        span = positive_max - positive_min
        offset = span * 0.06 if span > 0 else 1.0
        bar_x = positive_max + offset
        width_inf = offset * 0.4
        prob_inf = infinite_mask.sum() / total
        height_inf = prob_inf / width_inf

        ax.bar(
            bar_x,
            height_inf,
            width=width_inf,
            color='red',
            alpha=0.6,
            bottom=ymin,
        )
        infinite_bar_top = ymin + height_inf
        ax.text(
            bar_x,
            -0.008,
            r"$\infty$",
            transform=ax.get_xaxis_transform(),
            ha='center',
            va='top',
            color='red',
            fontsize=20,
        )
        ax.set_xlim(positive_min, bar_x + offset)
        ax.set_xticks([tick for tick in ax.get_xticks() if tick <= positive_max])

        if infinite_bar_top > ymax:
            ax.set_ylim(ymin, infinite_bar_top * 1.3)

    plt.title(file_name, fontsize=24)
    plt.savefig(f'/home/yirongwn/proj/trace-gen/figures/{file_name}_irds.pdf',
                format='pdf', bbox_inches='tight')
    plt.show()

def plot_ttls(file_name, ttls):
    values, counts = np.unique(ttls, return_counts=True)
    palette = colors
    fig, ax = plt.subplots(figsize=(6, 4.5))
    bins = np.linspace(values.min(), values.max(), 30)

    ax.hist(values, bins=bins, weights=counts, density=True,
            color=palette[1], lw=1.4, alpha=0.9, edgecolor='white')

    plt.title(file_name, fontsize=24)
    ax.set_yscale('log', base=10)
    ax.set_xlabel('TTL (seconds)', fontsize=22)
    ax.set_ylabel('PMF', fontsize=22)
    _fmt_axis(ax, use_log_y=True)

    plt.savefig(f'/home/yirongwn/proj/trace-gen/figures/{file_name}_ttls.pdf',
                format='pdf', bbox_inches='tight')
    plt.show()

from matplotlib.ticker import ScalarFormatter, LogFormatterSciNotation, LogLocator

def plot_key_freqs(file_name, keys):
    unique_keys, freq = np.unique(keys, return_counts=True)
    pmf = np.sort(freq.astype(float) / freq.sum())[::-1]
    ranks = np.arange(1, pmf.size + 1, dtype=float)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(ranks, pmf, color=colors[2], lw=1.4)
    ax.fill_between(ranks, pmf, color=colors[2], alpha=0.25)

    ax.set_yscale('log', base=10)
    ax.set_xlabel('Key rank', fontsize=22)
    ax.set_ylabel('PMF', fontsize=22)
    ax.set_title(file_name, fontsize=24)
    ax.tick_params(axis='both', which='major', labelsize=16)

    xfmt = ScalarFormatter(useMathText=True)
    xfmt.set_powerlimits((-3, 3))
    ax.xaxis.set_major_formatter(xfmt)
    ax.xaxis.get_offset_text().set_fontsize(16)

    ax.yaxis.set_major_locator(LogLocator(base=10, subs=np.arange(1, 10)))
    yfmt = LogFormatterSciNotation()
    yfmt.labelOnlyBase = False
    ax.yaxis.set_major_formatter(yfmt)
    ax.yaxis.get_offset_text().set_fontsize(16)

    plt.savefig(f'/home/yirongwn/proj/trace-gen/figures/{file_name}_key_freqs.pdf',
                format='pdf', bbox_inches='tight')
    plt.show()

def summarize_keys(ttls: np.ndarray,
                   keys: np.ndarray,
                   iads: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if keys.size == 0:
        return (np.empty(0, dtype=np.float64),
                np.empty(0, dtype=np.int64),
                np.empty(0, dtype=ttls.dtype))

    n_keys = int(keys.max()) + 1

    freq = np.bincount(keys, minlength=n_keys).astype(np.int64, copy=False)

    finite = iads >= 0
    iad_sum = np.bincount(keys[finite], weights=iads[finite], minlength=n_keys)
    finite_hits = np.bincount(keys[finite], minlength=n_keys)
    mean_iad = np.full(n_keys, np.nan, dtype=np.float64)
    mask = finite_hits > 0
    mean_iad[mask] = iad_sum[mask] / finite_hits[mask]

    first_idx = np.full(n_keys, keys.size, dtype=np.int64)
    np.minimum.at(first_idx, keys, np.arange(keys.size, dtype=np.int64))
    ttl_per_key = ttls[first_idx]

    return mean_iad, freq, ttl_per_key

# %%
ttls, keys, iads = proc_trc('106m106')
plot_irds('106m106', iads)
# %%
mean_iad106, freq106, ttl_per_key106 = summarize_keys(ttls, keys, iads)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
ax1.scatter(freq106, mean_iad106, alpha=0.5, color=colors[3])
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_xlabel('Key Frequency', fontsize=16)
ax1.set_ylabel('Mean IAD', fontsize=16)
ax2.scatter(ttl_per_key106, mean_iad106, alpha=0.5, color=colors[4])
ax2.set_xscale('log')
ax2.set_yscale('log')
ax2.set_xlabel('Key TTL', fontsize=16)
ax2.set_ylabel('Mean IAD', fontsize=16)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.show()