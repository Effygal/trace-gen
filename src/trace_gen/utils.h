#include <algorithm>
#include <fmt/color.h>
#include <numeric>
#include <vector>

template <typename T> using vec = std::vector<T>;
using i64 = int64_t;
using f64 = double;
using nvec = std::vector<i64>;
using str = std::string;

#define log_info(MSG, ...)                                                     \
    do {                                                                       \
        fmt::print(stderr,                                                     \
                   fg(fmt::terminal_color::cyan) | fmt::emphasis::bold,        \
                   "[INFO {}:{} {}] " MSG "\n", __FILE__, __LINE__, __func__,  \
                   ##__VA_ARGS__);                                             \
    } while (0)

#define log_fatal(MSG, ...)                                                    \
    do {                                                                       \
        fmt::print(stderr, fg(fmt::terminal_color::red) | fmt::emphasis::bold, \
                   "[FATAL {}:{} {}] " MSG "\n", __FILE__, __LINE__, __func__, \
                   ##__VA_ARGS__);                                             \
        std::abort();                                                          \
    } while (0)

#define ensure_fatal(COND, MSG, ...)                                           \
    do {                                                                       \
        if (!(COND)) {                                                         \
            fmt::print(stderr,                                                 \
                       fg(fmt::terminal_color::red) | fmt::emphasis::bold,     \
                       "[ERR {}:{} {}] " MSG "\n", __FILE__, __LINE__,         \
                       __func__, ##__VA_ARGS__);                               \
            std::abort();                                                      \
        }                                                                      \
    } while (0)

inline vec<str> split(std::string s, std::string delimiter)
{
    size_t pos_start = 0, pos_end, delim_len = delimiter.length();
    std::string token;
    std::vector<std::string> res;

    while ((pos_end = s.find(delimiter, pos_start)) != std::string::npos) {
        token = s.substr(pos_start, pos_end - pos_start);
        pos_start = pos_end + delim_len;
        res.push_back(token);
    }

    res.push_back(s.substr(pos_start));
    return res;
}

inline auto normalise_vec(vec<f64> &weights)
{
    auto sum = std::accumulate(weights.begin(), weights.end(), 0.0);
    for (auto &w : weights)
        w /= sum;
}
