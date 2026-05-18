/**
 * @file compress.hpp
 * @brief Single-block SHA-256 / SHA-512 compression (reduced-round capable).
 *
 * Each function implements one application of the compression function on one
 * 16-word message block, starting from an 8-word chaining state. The @p rounds
 * parameter limits how many of the (full) schedule rounds are executed; this
 * matches the original verifier's use for cryptanalysis on reduced rounds.
 */
#pragma once

#include "sha2/constants.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>

namespace sha2 {

namespace detail {

inline std::uint32_t rotr32(std::uint32_t value, unsigned bits)
{
    return (value >> bits) | (value << (32U - bits));
}

inline std::uint64_t rotr64(std::uint64_t value, unsigned bits)
{
    return (value >> bits) | (value << (64U - bits));
}

inline std::uint32_t ch32(std::uint32_t x, std::uint32_t y, std::uint32_t z)
{
    return (x & y) ^ (~x & z);
}

inline std::uint64_t ch64(std::uint64_t x, std::uint64_t y, std::uint64_t z)
{
    return (x & y) ^ (~x & z);
}

inline std::uint32_t maj32(std::uint32_t x, std::uint32_t y, std::uint32_t z)
{
    return (x & y) ^ (x & z) ^ (y & z);
}

inline std::uint64_t maj64(std::uint64_t x, std::uint64_t y, std::uint64_t z)
{
    return (x & y) ^ (x & z) ^ (y & z);
}

inline std::uint32_t big_sigma0_32(std::uint32_t x)
{
    return rotr32(x, 2U) ^ rotr32(x, 13U) ^ rotr32(x, 22U);
}

inline std::uint32_t big_sigma1_32(std::uint32_t x)
{
    return rotr32(x, 6U) ^ rotr32(x, 11U) ^ rotr32(x, 25U);
}

inline std::uint32_t small_sigma0_32(std::uint32_t x)
{
    return rotr32(x, 7U) ^ rotr32(x, 18U) ^ (x >> 3U);
}

inline std::uint32_t small_sigma1_32(std::uint32_t x)
{
    return rotr32(x, 17U) ^ rotr32(x, 19U) ^ (x >> 10U);
}

inline std::uint64_t big_sigma0_64(std::uint64_t x)
{
    return rotr64(x, 28U) ^ rotr64(x, 34U) ^ rotr64(x, 39U);
}

inline std::uint64_t big_sigma1_64(std::uint64_t x)
{
    return rotr64(x, 14U) ^ rotr64(x, 18U) ^ rotr64(x, 41U);
}

inline std::uint64_t small_sigma0_64(std::uint64_t x)
{
    return rotr64(x, 1U) ^ rotr64(x, 8U) ^ (x >> 7U);
}

inline std::uint64_t small_sigma1_64(std::uint64_t x)
{
    return rotr64(x, 19U) ^ rotr64(x, 61U) ^ (x >> 6U);
}

} // namespace detail

/**
 * One SHA-256 compression: `iv` is the incoming chaining state, `block` is W_0…W_15.
 * @param rounds Number of step rounds (clamped to at most 64).
 */
inline std::array<std::uint32_t, 8> sha256_compress(
    const std::array<std::uint32_t, 8> &iv,
    const std::array<std::uint32_t, 16> &block,
    std::size_t rounds = 64)
{
    rounds = std::min(rounds, kSha256RoundConstants.size());

    std::array<std::uint32_t, 64> w{};
    for (std::size_t i = 0; i < block.size(); ++i)
    {
        w[i] = block[i];
    }
    for (std::size_t i = 16; i < w.size(); ++i)
    {
        w[i] = detail::small_sigma1_32(w[i - 2]) + w[i - 7] +
               detail::small_sigma0_32(w[i - 15]) + w[i - 16];
    }

    std::uint32_t a = iv[0];
    std::uint32_t b = iv[1];
    std::uint32_t c = iv[2];
    std::uint32_t d = iv[3];
    std::uint32_t e = iv[4];
    std::uint32_t f = iv[5];
    std::uint32_t g = iv[6];
    std::uint32_t h = iv[7];

    for (std::size_t i = 0; i < rounds; ++i)
    {
        const std::uint32_t t1 = h + detail::big_sigma1_32(e) +
                                 detail::ch32(e, f, g) + kSha256RoundConstants[i] + w[i];
        const std::uint32_t t2 = detail::big_sigma0_32(a) + detail::maj32(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }

    return {a + iv[0], b + iv[1], c + iv[2], d + iv[3],
            e + iv[4], f + iv[5], g + iv[6], h + iv[7]};
}

/**
 * One SHA-512 compression: `iv` is the incoming chaining state, `block` is W_0…W_15.
 * @param rounds Number of step rounds (clamped to at most 80).
 */
inline std::array<std::uint64_t, 8> sha512_compress(
    const std::array<std::uint64_t, 8> &iv,
    const std::array<std::uint64_t, 16> &block,
    std::size_t rounds = 80)
{
    rounds = std::min(rounds, kSha512RoundConstants.size());

    std::array<std::uint64_t, 80> w{};
    for (std::size_t i = 0; i < block.size(); ++i)
    {
        w[i] = block[i];
    }
    for (std::size_t i = 16; i < w.size(); ++i)
    {
        w[i] = detail::small_sigma1_64(w[i - 2]) + w[i - 7] +
               detail::small_sigma0_64(w[i - 15]) + w[i - 16];
    }

    std::uint64_t a = iv[0];
    std::uint64_t b = iv[1];
    std::uint64_t c = iv[2];
    std::uint64_t d = iv[3];
    std::uint64_t e = iv[4];
    std::uint64_t f = iv[5];
    std::uint64_t g = iv[6];
    std::uint64_t h = iv[7];

    for (std::size_t i = 0; i < rounds; ++i)
    {
        const std::uint64_t t1 = h + detail::big_sigma1_64(e) +
                                 detail::ch64(e, f, g) + kSha512RoundConstants[i] + w[i];
        const std::uint64_t t2 = detail::big_sigma0_64(a) + detail::maj64(a, b, c);
        h = g;
        g = f;
        f = e;
        e = d + t1;
        d = c;
        c = b;
        b = a;
        a = t1 + t2;
    }

    return {a + iv[0], b + iv[1], c + iv[2], d + iv[3],
            e + iv[4], f + iv[5], g + iv[6], h + iv[7]};
}

} // namespace sha2
