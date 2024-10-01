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

auto zipf_dist(f64 alpha, i64 n, i64 max) -> dist
{
    std::vector<f64> weights;
    std::vector<std::uniform_int_distribution<i64>> intervals;
    for (f64 i = 1; i <= n; i++) {
        weights.push_back(1.0 / std::pow(i, alpha));
        intervals.push_back(std::uniform_int_distribution<i64>(i - 1, i));
    }
    normalise_vec(weights);

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

auto pareto_dist(f64 xm, f64 alpha, i64 n, i64 max) -> dist
{
    fmt::print("IRM: pareto: xm: {} n: {}\n", xm, n);

    std::vector<f64> weights;
    std::vector<std::uniform_int_distribution<i64>> intervals;
    for (f64 i = 1; i <= n; i++) {
        weights.push_back(std::pow(xm / i, alpha));
        intervals.push_back(std::uniform_int_distribution<i64>(i - 1, i));
    }
    normalise_vec(weights);

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

auto irdgen(i64 k, f64 epsilon, vec<i64> spikes) -> dist
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

    std::discrete_distribution<i64> dis(weights.begin(), weights.end());
    return [dis](std::mt19937_64 &rng) mutable { return dis(rng); };
}

// === Trace generation ===

struct tadr {
    i64 ird;
    i64 addr;
};
auto tadr_cmp = [](const tadr &a, const tadr &b) { return a.ird < b.ird; };

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
We take in 5 inputs:

- m: footprint size (number of unique addresses)
- n: length of trace (in addresses)
- p_irm: probability of the trace that is IRM (float between 0 and 1)
- f: distribution of IRD (f1 to f6, or inputs to fgen (k # of classes, indices
of spikes, and non-spike heights))
- g: distribution of IRM (zipf, pareto, uniform, normal)
 */
auto generate_trace(i64 addrs, i64 length, f64 p_irm, dist d_ird, dist d_irm,
                    std::mt19937_64 &rng)
{
    vec<tadr> irds;

    // for each address, associate with it an ird drawn from the ird dist
    for (i64 a = 0; a < addrs; a++)
        irds.push_back({.ird = d_ird(rng), .addr = a});

    // heapify the irds
    std::make_heap(irds.begin(), irds.end(), tadr_cmp);

    vec<i64> trace;
    for (i64 i = 0; i < length; i++) {
        std::uniform_real_distribution<> dis(0, 1);
        auto is_irm = dis(rng) < p_irm;

        // if it is IRM, draw from the IRM dist and continue
        if (is_irm) {
            auto addr = d_irm(rng);
            assert(addr < addrs);
            trace.push_back(addr);
            continue;
        }

        // otherwise, draw from the IRD dist
        auto ird_sample = d_ird(rng);
        assert(ird_sample >= 0 && ird_sample < addrs);

        auto min_ird = heappop(irds);
        trace.push_back(min_ird.addr);
        heappush(irds, min_ird.ird + ird_sample, min_ird.addr);
    }

    return trace;
}

// === Parsing and user io ===

auto parse_fgen(vec<str> args)
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

    return irdgen(k, epsilon, spike_idxs);
}

auto parse_ird(str s)
{
    if (s == "b")
        return irdgen(20, 0.005, {0, 3});
    if (s == "c")
        return irdgen(20, 0.005, {2, 9});
    if (s == "d")
        return irdgen(5, 0.01, {0, 4});
    if (s == "e")
        return irdgen(20, 0.005, {1});
    if (s == "f")
        return irdgen(20, 0.01, {2});

    auto args = split(s, ":");
    if (args[0] == "fgen")
        return parse_fgen(args);

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

int main(int argc, char **argv)
{
    namespace po = boost::program_options;

    po::options_description desc("Allowed options");

    i64 length, addrs, seed;
    f64 p_irm;
    str ird_arg, irm_arg;

    // clang-format off
    desc.add_options()
        ("help,h", "Produce this message")
        ("addresses,m", po::value<i64>(&addrs)->required(),
            "Footprint size (number of unique addresses)")
        ("length,n", po::value<i64>(&length)->required(),
            "Length of trace (in addresses)")
        ("p_irm,p", po::value<f64>(&p_irm)->required(),
            "Probability of the trace that is IRM (float between 0 and 1)")
        // only support f1-f6 for now
        ("ird,f", po::value<str>(&ird_arg)->default_value("b"),
            "IRD distribution. Can be one of the pre-specified distributions (b to f) "
            "or inputs to fgen (k # of classes, non-spike heights, and indices of spikes) "
            "separated by columns. Example: -f b or -f fgen:10000:0.00001:3,5,10,20")
        ("irm,g", po::value<str>(&irm_arg)->default_value("zipf:1.2,20"),
            "IRM distribution. Can be: zipf:alpha,n, pareto:xm,a,n, uniform:max, normal:mean,stddev). ")
        ("seed,s", po::value<i64>(&seed)->default_value(42),
            "RNG seed");
    ;
    // clang-format on

    po::variables_map vm;
    try {
        po::store(po::parse_command_line(argc, argv, desc), vm);
    } catch (std::exception &e) {
        fmt::print("Error: {}\n", e.what());
        desc.print(std::cout);
        return 1;
    }
    po::notify(vm);

    if (vm.count("help")) {
        desc.print(std::cout);
        return 1;
    }

    fmt::print("Generating trace with the following parameters:\n");
    fmt::print("Addresses: {}\n", addrs);
    fmt::print("Length: {}\n", length);
    fmt::print("Probability of IRM: {}\n", p_irm);
    fmt::print("Seed: {}\n", seed);

    auto ird = parse_ird(ird_arg);
    auto irm = parse_irm(irm_arg, addrs);

    std::mt19937_64 rng(seed);
    auto trace = generate_trace(addrs, length, p_irm, ird, irm, rng);
    for (auto t : trace)
        fmt::print("{}\n", t);

    auto d = ird;
    for (int i = 0; i < 20; i++)
        fmt::print("{}\n", d(rng));

    return 0;
}