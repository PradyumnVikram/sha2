/**
 * @file format.hpp
 * @brief Hex formatting helpers matching the legacy verifier's textual output.
 */
#pragma once

#include <array>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string>

namespace sha2 {

/// Format a block or IV as space-separated `0x…` words (32-bit).
inline std::string format_words_hex(const std::array<std::uint32_t, 16> &words)
{
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t i = 0; i < words.size(); ++i)
    {
        if (i != 0)
        {
            out << ' ';
        }
        out << "0x" << std::setw(8) << static_cast<std::uint32_t>(words[i]);
    }
    return out.str();
}

/// Format a block or IV as space-separated `0x…` words (64-bit).
inline std::string format_words_hex(const std::array<std::uint64_t, 16> &words)
{
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t i = 0; i < words.size(); ++i)
    {
        if (i != 0)
        {
            out << ' ';
        }
        out << "0x" << std::setw(16) << static_cast<unsigned long long>(words[i]);
    }
    return out.str();
}

/// Format eight 32-bit chaining words without `0x` prefix (legacy hash line style).
inline std::string format_state_hex(const std::array<std::uint32_t, 8> &state)
{
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t i = 0; i < state.size(); ++i)
    {
        if (i != 0)
        {
            out << ' ';
        }
        out << std::setw(8) << state[i];
    }
    return out.str();
}

/// Format eight 64-bit chaining words without `0x` prefix.
inline std::string format_state_hex(const std::array<std::uint64_t, 8> &state)
{
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t i = 0; i < state.size(); ++i)
    {
        if (i != 0)
        {
            out << ' ';
        }
        out << std::setw(16) << static_cast<unsigned long long>(state[i]);
    }
    return out.str();
}

/// Format eight-word IV with `0x` prefix per word (matches IV print style).
inline std::string format_iv_hex(const std::array<std::uint32_t, 8> &iv)
{
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t i = 0; i < iv.size(); ++i)
    {
        if (i != 0)
        {
            out << ' ';
        }
        out << "0x" << std::setw(8) << static_cast<std::uint32_t>(iv[i]);
    }
    return out.str();
}

inline std::string format_iv_hex(const std::array<std::uint64_t, 8> &iv)
{
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (std::size_t i = 0; i < iv.size(); ++i)
    {
        if (i != 0)
        {
            out << ' ';
        }
        out << "0x" << std::setw(16) << static_cast<unsigned long long>(iv[i]);
    }
    return out.str();
}

} // namespace sha2
