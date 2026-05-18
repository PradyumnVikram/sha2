/**
 * @file verifier.hpp
 * @brief Run collision verification and emit the same report shape as the legacy tool.
 */
#pragma once

#include "sha2/compress.hpp"
#include "sha2/config.hpp"
#include "sha2/format.hpp"

#include <iostream>
#include <string>

namespace sha2 {

namespace detail {

inline std::string mode_banner(VerificationMode m)
{
    switch (m)
    {
    case VerificationMode::FreeStart:
        return "free-start collision verification";
    case VerificationMode::SemiFreeStart:
        return "semi-free-start collision verification";
    case VerificationMode::StandardIvCollision:
        return "standard initial value collision verification";
    }
    return {};
}

} // namespace detail

template <typename Word>
using Block = std::array<Word, 16>;

template <typename Word>
using State = std::array<Word, 8>;

template <typename Word>
using CompressFn = State<Word> (*)(const State<Word> &, const Block<Word> &, std::size_t);

/**
 * Apply optional shared prefix block MSG0 to both paths.
 * When Message_count is 1, `initial` is returned unchanged.
 */
template <typename Word>
State<Word> chain_prefix(const ParsedConfig &cfg, const State<Word> &initial,
                         std::size_t rounds, CompressFn<Word> compress)
{
    if (cfg.pipeline == MessagePipeline::SingleBlock)
    {
        return initial;
    }
    const auto msg0 = detail::parse_hex_word_array<Word, 16>(cfg.msg0_text);
    return compress(initial, msg0, rounds);
}

template <typename Word>
void print_iv_section(std::ostream &os, VerificationMode mode,
                      const State<Word> &iv1, const State<Word> &iv2)
{
    if (mode == VerificationMode::FreeStart)
    {
        os << "IV1: " << format_iv_hex(iv1) << '\n';
        os << "IV2: " << format_iv_hex(iv2) << '\n';
    }
    else
    {
        os << "IV: " << format_iv_hex(iv1) << '\n';
    }
}

template <typename Word>
int verify_and_report(std::ostream &os, const ParsedConfig &cfg)
{
    CompressFn<Word> compress{};
    const char *version_label = nullptr;
    State<Word> iv_path1{};
    State<Word> iv_path2{};

    if constexpr (sizeof(Word) == sizeof(std::uint32_t))
    {
        compress = sha256_compress;
        version_label = "SHA256";

        switch (cfg.mode)
        {
        case VerificationMode::FreeStart:
            iv_path1 = detail::parse_hex_word_array<std::uint32_t, 8>(cfg.iv1_text);
            iv_path2 = detail::parse_hex_word_array<std::uint32_t, 8>(cfg.iv2_text);
            break;
        case VerificationMode::SemiFreeStart:
            iv_path1 = detail::parse_hex_word_array<std::uint32_t, 8>(cfg.iv_text);
            iv_path2 = iv_path1;
            break;
        case VerificationMode::StandardIvCollision:
            iv_path1 = kSha256StandardIv;
            iv_path2 = kSha256StandardIv;
            break;
        }
    }
    else
    {
        compress = sha512_compress;
        version_label = "SHA512";

        switch (cfg.mode)
        {
        case VerificationMode::FreeStart:
            iv_path1 = detail::parse_hex_word_array<std::uint64_t, 8>(cfg.iv1_text);
            iv_path2 = detail::parse_hex_word_array<std::uint64_t, 8>(cfg.iv2_text);
            break;
        case VerificationMode::SemiFreeStart:
            iv_path1 = detail::parse_hex_word_array<std::uint64_t, 8>(cfg.iv_text);
            iv_path2 = iv_path1;
            break;
        case VerificationMode::StandardIvCollision:
            iv_path1 = kSha512StandardIv;
            iv_path2 = kSha512StandardIv;
            break;
        }
    }

    const auto msg1 = detail::parse_hex_word_array<Word, 16>(cfg.msg1_text);
    const auto msg2 = detail::parse_hex_word_array<Word, 16>(cfg.msg2_text);

    const State<Word> after_prefix1 = chain_prefix(cfg, iv_path1, cfg.rounds, compress);
    const State<Word> after_prefix2 = chain_prefix(cfg, iv_path2, cfg.rounds, compress);

    const State<Word> final1 = compress(after_prefix1, msg1, cfg.rounds);
    const State<Word> final2 = compress(after_prefix2, msg2, cfg.rounds);

    os << "Version: " << version_label << '\n';
    os << "Message_count: " << (cfg.pipeline == MessagePipeline::SingleBlock ? 1 : 2)
       << '\n';
    os << "Round: " << cfg.rounds << '\n';
    os << "Type: " << detail::mode_banner(cfg.mode) << '\n';

    print_iv_section(os, cfg.mode, iv_path1, iv_path2);

    if (cfg.pipeline == MessagePipeline::TwoBlock)
    {
        const auto msg0 = detail::parse_hex_word_array<Word, 16>(cfg.msg0_text);
        os << "MSG0: " << format_words_hex(msg0) << '\n';
        os << "MSG0 Output for MSG1: " << format_state_hex(after_prefix1) << '\n';
        os << "MSG0 Output for MSG2: " << format_state_hex(after_prefix2) << '\n';
    }

    os << "MSG1: " << format_words_hex(msg1) << '\n';
    os << "MSG2: " << format_words_hex(msg2) << '\n';
    os << "MSG1 Hash: " << format_state_hex(final1) << '\n';
    os << "MSG2 Hash: " << format_state_hex(final2) << '\n';
    os << "Collision: " << (final1 == final2 ? "YES" : "NO") << '\n';

    return 0;
}

inline int run_verification(std::ostream &os, std::ostream &err,
                            const ParsedConfig &cfg)
{
    switch (cfg.variant)
    {
    case HashVariant::Sha256:
        return verify_and_report<std::uint32_t>(os, cfg);
    case HashVariant::Sha512:
        return verify_and_report<std::uint64_t>(os, cfg);
    }
    err << "Unsupported hash variant\n";
    return 1;
}

} // namespace sha2
