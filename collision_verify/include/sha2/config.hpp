/**
 * @file config.hpp
 * @brief Parse `key: value;` configuration files for collision verification.
 *
 * Format matches the original `verify_result` tool: one field per line, optional
 * trailing semicolon on values. Empty lines and lines without ':' are skipped.
 */
#pragma once

#include <array>
#include <cctype>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>

namespace sha2 {

enum class HashVariant
{
    Sha256,
    Sha512,
};

/** Free-start: compress MSG1 from IV1 and MSG2 from IV2. */
enum class VerificationMode
{
    FreeStart,
    /** Same IV on both paths (semi-free-start). */
    SemiFreeStart,
    /** Both paths use the algorithm standard IV (FIPS 180-4). */
    StandardIvCollision,
};

enum class MessagePipeline
{
    /** IV → MSG1 and IV → MSG2 in parallel (no MSG0). */
    SingleBlock,
    /** IV → MSG0 → MSG1 and IV → MSG0 → MSG2 (MSG0 shared). */
    TwoBlock,
};

struct ParsedConfig
{
    HashVariant variant{};
    MessagePipeline pipeline{};
    VerificationMode mode{};
    std::size_t rounds{};

    /** Present when pipeline == TwoBlock. */
    std::string msg0_text;

    std::string msg1_text;
    std::string msg2_text;

    /** IV1 / IV2 hex lists for FreeStart; IV hex for SemiFreeStart; unused for StandardIvCollision. */
    std::string iv1_text;
    std::string iv2_text;
    std::string iv_text;
};

namespace detail {

inline std::string trim(const std::string &s)
{
    std::size_t begin = 0;
    while (begin < s.size() &&
           std::isspace(static_cast<unsigned char>(s[begin])))
    {
        ++begin;
    }
    std::size_t end = s.size();
    while (end > begin && std::isspace(static_cast<unsigned char>(s[end - 1])))
    {
        --end;
    }
    return s.substr(begin, end - begin);
}

inline std::string to_upper_ascii(std::string s)
{
    for (char &ch : s)
    {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

inline HashVariant parse_variant(const std::string &raw)
{
    const std::string n = to_upper_ascii(trim(raw));
    if (n == "SHA256" || n == "SHA-256")
    {
        return HashVariant::Sha256;
    }
    if (n == "SHA512" || n == "SHA-512")
    {
        return HashVariant::Sha512;
    }
    throw std::runtime_error("Unsupported Version: " + raw);
}

inline VerificationMode parse_mode(const std::string &raw)
{
    const std::string t = trim(raw);
    const std::string n = to_upper_ascii(t);

    if (n == "SEMI-FREE-START" || n == "SEMI_FREE_START" || n == "SEMIFREESTART" ||
        n == "SFS" || t == "semi-free-start")
    {
        return VerificationMode::SemiFreeStart;
    }
    if (n == "COLLISION")
    {
        return VerificationMode::StandardIvCollision;
    }
    if (n == "FREE-START" || n == "FREE_START" || n == "FREESTART" || n == "FS" ||
        t == "free-start")
    {
        return VerificationMode::FreeStart;
    }
    throw std::runtime_error("Unsupported Type: " + raw);
}

inline MessagePipeline parse_message_count(const std::string &raw)
{
    const unsigned long v = std::stoul(trim(raw));
    if (v == 1)
    {
        return MessagePipeline::SingleBlock;
    }
    if (v == 2)
    {
        return MessagePipeline::TwoBlock;
    }
    throw std::runtime_error("Unsupported Message_count: " + raw);
}

inline std::map<std::string, std::string> load_key_values(const std::string &path)
{
    std::ifstream input(path);
    if (!input)
    {
        throw std::runtime_error("Failed to open config file: " + path);
    }

    std::map<std::string, std::string> config;
    std::string line;
    while (std::getline(input, line))
    {
        line = trim(line);
        if (line.empty())
        {
            continue;
        }

        const auto colon = line.find(':');
        if (colon == std::string::npos)
        {
            continue;
        }

        std::string key = trim(line.substr(0, colon));
        std::string value = trim(line.substr(colon + 1));
        if (!value.empty() && value.back() == ';')
        {
            value.pop_back();
            value = trim(value);
        }
        config[key] = value;
    }
    return config;
}

inline std::string require_field(const std::map<std::string, std::string> &m,
                                 const std::string &key)
{
    const auto it = m.find(key);
    if (it == m.end())
    {
        throw std::runtime_error("Missing field: " + key);
    }
    return it->second;
}

template <typename T, std::size_t N>
std::array<T, N> parse_hex_word_array(const std::string &text)
{
    std::array<T, N> values{};
    std::stringstream stream(text);
    std::string token;
    std::size_t index = 0;

    while (std::getline(stream, token, ','))
    {
        token = trim(token);
        if (token.empty())
        {
            continue;
        }
        if (index >= N)
        {
            throw std::runtime_error("Too many data words were provided");
        }
        values[index++] = static_cast<T>(std::stoull(token, nullptr, 0));
    }

    if (index != N)
    {
        throw std::runtime_error("Incorrect number of data words: expected " +
                                 std::to_string(N) + ", got " + std::to_string(index));
    }
    return values;
}

} // namespace detail

/**
 * Read and validate a config file into a ParsedConfig. Does not parse MSG/IV hex
 * into arrays yet—call the appropriate `parse_hex_*` when building state.
 */
inline ParsedConfig parse_config_file(const std::string &path)
{
    const auto kv = detail::load_key_values(path);
    ParsedConfig out{};
    out.variant = detail::parse_variant(detail::require_field(kv, "Version"));
    out.pipeline = detail::parse_message_count(detail::require_field(kv, "Message_count"));
    out.rounds = static_cast<std::size_t>(std::stoul(detail::require_field(kv, "Round")));
    out.mode = detail::parse_mode(detail::require_field(kv, "Type"));

    out.msg1_text = detail::require_field(kv, "MSG1");
    out.msg2_text = detail::require_field(kv, "MSG2");

    if (out.pipeline == MessagePipeline::TwoBlock)
    {
        out.msg0_text = detail::require_field(kv, "MSG0");
    }

    switch (out.mode)
    {
    case VerificationMode::FreeStart:
        out.iv1_text = detail::require_field(kv, "IV1");
        out.iv2_text = detail::require_field(kv, "IV2");
        break;
    case VerificationMode::SemiFreeStart:
        out.iv_text = detail::require_field(kv, "IV");
        break;
    case VerificationMode::StandardIvCollision:
        break;
    }

    return out;
}

} // namespace sha2
