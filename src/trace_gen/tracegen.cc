#include <algorithm>
#include <boost/program_options.hpp>
#include <boost/program_options/options_description.hpp>
#include <boost/program_options/positional_options.hpp>
#include <boost/program_options/variables_map.hpp>
#include <fmt/core.h>
#include <fmt/format.h>
#include <fmt/printf.h>
#include <iostream>
#include <random>
#include <vector>

#include "utils.h"

using dist = std::function<i64(std::mt19937_64 &)>;

auto get_intervals(i64 classes, i64 max)
{
    assert(classes > 0 && max > 0 && classes <= max);

    vec<std::uniform_int_distribution<i64>> intervals;
    auto width = max / classes;

    for (i64 i = 1; i <= classes; i++) {
        auto lower = (i - 1) * width;
        auto upper = (i - 0) * width - 1;
        upper = std::min(upper, max - 1);
        intervals.push_back(std::uniform_int_distribution<i64>(lower, upper));
    }
    return intervals;
}

auto normal_dist(f64 mean, f64 stddev, i64 max) -> dist
{
    std::normal_distribution<f64> dis(mean, stddev);
    return [dis, max](std::mt19937_64 &rng) mutable -> i64 {
        auto sample = dis(rng);
        if (sample < 0)
            return 0;
        if (sample > max)
            return max;
        return (i64)std::round(sample);
    };
}

auto zipf_dist(f64 alpha, i64 classes, i64 max) -> dist
{
    assert(alpha > 0 && classes > 0);
    fmt::print("IRM: zipf: alpha: {} n: {}\n", alpha, classes);

    auto intervals = get_intervals(classes, max);
    std::vector<f64> weights;
    for (f64 i = 1; i <= classes; i++)
        weights.push_back(1.0 / std::pow(i, alpha));
    normalise_vec(weights);
    assert(weights.size() == intervals.size());

    std::discrete_distribution<i64> dis(weights.begin(), weights.end());
    return [dis, ivs = std::move(intervals)](std::mt19937_64 &rng) mutable {
        auto idx = dis(rng);
        return ivs[idx](rng);
    };
}

auto uniform_dist(i64 max) -> dist
{
    std::uniform_int_distribution<i64> dis(0, max - 1);
    return [dis](std::mt19937_64 &rng) mutable { return dis(rng); };
}

auto pareto_dist(f64 xm, f64 alpha, i64 classes, i64 max) -> dist
{
    assert(xm > 0 && alpha > 0 && classes > 0);
    fmt::print("IRM: pareto: xm: {} n: {}\n", xm, classes);

    auto intervals = get_intervals(classes, max);
    std::vector<f64> weights;
    for (f64 i = 1; i <= classes; i++)
        weights.push_back(std::pow(xm / i, alpha));
    normalise_vec(weights);
    assert(weights.size() == intervals.size());

    std::discrete_distribution<i64> dis(weights.begin(), weights.end());
    return [dis, ivs = std::move(intervals)](std::mt19937_64 &rng) mutable {
        auto idx = dis(rng);
        return ivs[idx](rng);
    };
}

auto sequential_dist() -> dist
{
    fmt::print("IRM: sequential\n");
    i64 i = 0;
    return [i](std::mt19937_64 &rng) mutable { return i++; };
}

auto irdgen(i64 k, f64 epsilon, vec<i64> spikes, i64 unique_addrs) -> dist
{
    vec<f64> weights;
    for (i64 i = 0; i < k; i++)
        weights.push_back(epsilon);
    for (auto s : spikes)
        weights[s] = 1 - epsilon;
    normalise_vec(weights);

    fmt::print("IRD: k: {} epsilon: {} spikes: ", k, epsilon);
    for (auto s : spikes)
        fmt::print("{} ", s);
    fmt::print("\n");

    std::discrete_distribution<i64> bw_dis(weights.begin(), weights.end());

    // these weights are actually of another space of bins
    // for example, fgen 5 0.1 (1 3)
    // gets you a distribution over the bins of [0.1 0.9 0.1 0.9 0.1]
    // (before normalisation)
    // but then we have to project this up to a space of 0 to tmax
    // each bin is weighted by its index + 0.5, and each bin is
    // determined by some weird formulas i don't understand

    f64 weighted_sum = 0;
    for(i64 i = 0; i < weights.size(); i++)
        // i don't understand this formula but sure
        weighted_sum += weights[i] * (i + 0.5);

    f64 tmax = unique_addrs * k / weighted_sum;
    auto bins = get_intervals(k, tmax);

    return [bw_dis,bins](std::mt19937_64 &rng) mutable {
        auto i_bin = bw_dis(rng);
        return bins[i_bin](rng);
    };
}

// === Trace generation ===

struct tadr {
    i64 ird;
    i64 addr;
};

struct trace_entry {
    i64 addr;
    i64 size;
    bool is_read;
};

auto tadr_cmp(const tadr &a, const tadr &b) { return a.ird > b.ird; };

auto heappop(vec<tadr> &heap)
{
    std::pop_heap(heap.begin(), heap.end(), tadr_cmp);
    auto min = heap.back();
    heap.pop_back();
    return min;
}

auto heappush(vec<tadr> &heap, i64 ird, i64 addr)
{
    heap.push_back({.ird = ird, .addr = addr});
    std::push_heap(heap.begin(), heap.end(), tadr_cmp);
}

/**
We take in the following arguments:

- addrs: footprint size (number of unique addresses)
- length: length of trace (in addresses)
- p_irm: probability of the trace that is IRM (float between 0 and 1)
- d_ird: function used to generate IRDs
- d_irm: function used to generate IRMs
- rng: random number generator
 */
auto gen_addresses(i64 addrs, i64 length, f64 p_irm, dist d_ird, dist d_irm,
                   std::mt19937_64 &rng)
{
    vec<tadr> irds;

    // for each address, associate with it an ird drawn from the ird dist
    for (i64 a = 0; a < addrs; a++)
        irds.push_back({.ird = d_ird(rng), .addr = a});

    // heapify the irds
    std::make_heap(irds.begin(), irds.end(), tadr_cmp);

    std::uniform_real_distribution<> d_is_irm(0, 1);
    vec<i64> trace;
    for (i64 i = 0; i < length; i++) {
        auto is_irm = d_is_irm(rng) < p_irm;

        // if it is IRM, draw from the IRM dist and continue
        if (is_irm) {
            auto addr = d_irm(rng);
            assert(addr < addrs);
            trace.push_back(addr);
            continue;
        }

        // otherwise, draw from the IRD dist
        auto ird_sample = d_ird(rng);
        // assert(ird_sample >= 0 && ird_sample < addrs);

        auto min_ird = heappop(irds);
        trace.push_back(min_ird.addr);
        heappush(irds, min_ird.ird + ird_sample, min_ird.addr);
    }

    return trace;
}

// === Parsing and user io ===

auto parse_fgen(vec<str> args, i64 unique_addrs)
{
    assert(args[0] == "fgen");
    ensure_fatal(args.size() == 4,
                 "fgen requires 3 arguments -f fgen:k:epsilon:spikes");

    auto [k, epsilon, spikes_str] =
        std::make_tuple(std::stoi(args[1]), std::stod(args[2]), args[3]);
    auto spikes = split(spikes_str, ",");
    vec<i64> spike_idxs;
    for (auto s : spikes)
        spike_idxs.push_back(std::stoi(s));

    return irdgen(k, epsilon, spike_idxs, unique_addrs);
}

auto parse_ird(str s, i64 unique_addrs)
{
    if (s == "b")
        return irdgen(20, 0.005, {0, 3}, unique_addrs);
    if (s == "c")
        return irdgen(20, 0.005, {2, 9}, unique_addrs);
    if (s == "d")
        return irdgen(5, 0.01, {0, 4}, unique_addrs);
    if (s == "e")
        return irdgen(20, 0.005, {1}, unique_addrs);
    if (s == "f")
        return irdgen(20, 0.01, {2}, unique_addrs);

    auto args = split(s, ":");
    if (args[0] == "fgen")
        return parse_fgen(args, unique_addrs);

    std::cerr << "Invalid dist string: " << s << std::endl;
    exit(1);
}

auto parse_irm(str dist_str, i64 max) -> dist
{
    auto args = split(dist_str, ":");
    ensure_fatal(args.size() == 2, "Invalid dist string: {} ", dist_str);

    auto dist_type = args[0];
    auto dist_args = split(args[1], ",");

    if (dist_type == "pareto") {
        ensure_fatal(dist_args.size() == 3, "Pareto dist requires 3 args");
        auto xm = std::stod(dist_args[0]);
        auto alpha = std::stod(dist_args[1]);
        auto n = std::stoi(dist_args[2]);
        log_info("Pareto dist: xm: {} alpha: {} n: {}", xm, alpha, n);

        return pareto_dist(xm, alpha, n, max);
    }

    if (dist_type == "zipf") {
        ensure_fatal(dist_args.size() == 2, "Zipf dist requires 2 args");
        auto alpha = std::stod(dist_args[0]);
        auto n = std::stoi(dist_args[1]);
        log_info("Zipf dist: alpha: {} n: {}", alpha, n);

        return zipf_dist(alpha, n, max);
    }

    if (dist_type == "uniform") {
        log_info("Uniform dist: max: {}", max);
        return uniform_dist(max);
    }

    if (dist_type == "normal") {
        ensure_fatal(dist_args.size() == 2, "Normal dist requires 2 args");
        auto mu = std::stod(dist_args[0]);
        auto sigma = std::stod(dist_args[1]);
        log_info("Normal dist: mu: {} sigma: {}", mu, sigma);

        return normal_dist(mu, sigma, max);
    }

    log_fatal("Invalid dist type: {}", dist_type);
}

auto parse_request_sizes(str arg) -> dist
{
    auto parts = split(arg, ":");
    ensure_fatal(parts.size() == 2, "Invalid size dist string: {}", arg);

    auto weights = split(parts[0], ",");
    auto sizes = split(parts[1], ",");
    ensure_fatal(weights.size() == sizes.size(),
                 "Unequal number of weights and sizes: {}", arg);

    vec<f64> w;
    vec<i64> s;
    for (auto x : weights)
        w.push_back(std::stod(x));
    for (auto x : sizes)
        s.push_back(std::stoi(x));
    normalise_vec(w);

    std::discrete_distribution<i64> dis(w.begin(), w.end());
    return [dis, s](std::mt19937_64 &rng) mutable {
        auto idx = dis(rng);
        return s[idx];
    };
}

int main(int argc, char **argv)
{
    // return main2(argc, argv);
    namespace po = boost::program_options;

    po::options_description desc("Allowed options");

    i64 length, num_addrs, seed, blocksize;
    f64 p_irm, frac_read;
    str ird_arg, irm_arg, sizedist_arg;

    // clang-format off
    desc.add_options()
        ("help,h", "Produce this message")
        ("addresses,m", po::value<i64>(&num_addrs)->required(), "Footprint size (number of unique addresses)")
        ("length,n", po::value<i64>(&length)->required(), "Length of trace (in addresses)")
        ("p_irm,p", po::value<f64>(&p_irm)->required(), "Probability of the trace that is IRM (float between 0 and 1)")
        ("seed,s", po::value<i64>(&seed)->default_value(42), "RNG seed")
        ("blocksize,b", po::value<i64>(&blocksize)->default_value(4096), "Size of a block in bytes")
        ("ird,f", po::value<str>(&ird_arg)->default_value("b"),
            "IRD distribution. Can be one of the pre-specified distributions (b to f) "
            "or inputs to fgen (k # of classes, non-spike heights, and indices of spikes) "
            "separated by columns. Example: -f b or -f fgen:10000:0.00001:3,5,10,20")
        ("irm,g", po::value<str>(&irm_arg)->default_value("zipf:1.2,20"),
            "IRM distribution. Can be: zipf:alpha,n, pareto:xm,a,n, uniform:max, normal:mean,stddev). ")
        ("rwratio,r", po::value<f64>(&frac_read)->default_value(1),
            "Fraction of addresses that are reads (vs writes)")
        ("sizedist,z", po::value<str>(&sizedist_arg)->default_value("1:1"),
            "Distribution of request sizes in blocks."
            "Specified as a list of weights (floats) followed by a list of sizes in blocks (ints)."
            "Ex: 1,1,1:1,3,4 means equal chance of 1, 3, or 4-block requests")
    ;
    // clang-format on

    po::variables_map vm;
    try {
        po::store(po::parse_command_line(argc, argv, desc), vm);

        if (vm.count("help")) {
            desc.print(std::cout);
            return 1;
        }
    } catch (std::exception &e) {
        fmt::print("Error: {}\n", e.what());
        desc.print(std::cout);
        return 1;
    }
    po::notify(vm);

    fmt::print("Generating trace with the following parameters:\n");
    fmt::print("Addresses: {}\n", num_addrs);
    fmt::print("Length: {}\n", length);
    fmt::print("Probability of IRM: {}\n", p_irm);
    fmt::print("Seed: {}\n", seed);

    auto ird = parse_ird(ird_arg, num_addrs);
    auto irm = parse_irm(irm_arg, num_addrs);
    auto sizedist = parse_request_sizes(sizedist_arg);

    std::mt19937_64 rng(seed);
    auto addrs = gen_addresses(num_addrs, length, p_irm, ird, irm, rng);

    // post-process to include r/w, size, and byte offset (instead of block)
    std::uniform_real_distribution<> d_is_read(0, 1);

    for (auto addr : addrs) {
        auto is_read = (d_is_read(rng) < frac_read);
        auto size = sizedist(rng);
        fmt::print("{:d} {} {}\n", !is_read, size * blocksize,
                   addr * blocksize);
    }

    return 0;
}
