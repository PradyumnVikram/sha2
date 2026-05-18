#include "hash_utils.h"

#include <array>
#include <cctype>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>

namespace
{

    std::string trim(const std::string &value)
    {
        std::size_t begin = 0;
        while (begin < value.size() &&
               std::isspace(static_cast<unsigned char>(value[begin])))
        {
            ++begin;
        }

        std::size_t end = value.size();
        while (end > begin &&
               std::isspace(static_cast<unsigned char>(value[end - 1])))
        {
            --end;
        }

        return value.substr(begin, end - begin);
    }

    std::string to_upper_ascii(std::string value)
    {
        for (char &ch : value)
        {
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        }
        return value;
    }

    std::map<std::string, std::string> parse_config(const std::string &path)
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

            const std::size_t colon_pos = line.find(':');
            if (colon_pos == std::string::npos)
            {
                continue;
            }

            std::string key = trim(line.substr(0, colon_pos));
            std::string value = trim(line.substr(colon_pos + 1));
            if (!value.empty() && value.back() == ';')
            {
                value.pop_back();
                value = trim(value);
            }
            config[key] = value;
        }

        return config;
    }

    template <typename T, std::size_t N>
    std::array<T, N> parse_hex_array(const std::string &text)
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
                                     std::to_string(N) + ", got " +
                                     std::to_string(index));
        }

        return values;
    }

    std::string read_field(const std::map<std::string, std::string> &config,
                           const std::string &key)
    {
        const auto it = config.find(key);
        if (it == config.end())
        {
            throw std::runtime_error("Missing field: " + key);
        }
        return it->second;
    }

    std::string normalize_version(const std::string &version)
    {
        const std::string normalized = to_upper_ascii(trim(version));
        if (normalized == "SHA256" || normalized == "SHA-256")
        {
            return "SHA256";
        }
        if (normalized == "SHA512" || normalized == "SHA-512")
        {
            return "SHA512";
        }
        throw std::runtime_error("Unsupported Version: " + version);
    }

    std::string normalize_type(const std::string &type)
    {
        const std::string trimmed = trim(type);
        const std::string normalized = to_upper_ascii(trimmed);

        if (normalized == "SEMI-FREE-START" || normalized == "SEMI_FREE_START" ||
            normalized == "SEMIFREESTART" || normalized == "SFS" ||
            trimmed == "semi-free-start")
        {
            return "SEMI_FREE_START";
        }
        if (normalized == "COLLISION")
        {
            return "Collision";
        }

        if (normalized == "FREE-START" || normalized == "FREE_START" ||
            normalized == "FREESTART" || normalized == "FS" ||
            trimmed == "free-start")
        {
            return "FREE_START";
        }

        throw std::runtime_error("Unsupported Type: " + type);
    }

    template <typename T, std::size_t N>
    std::string format_word_array(const std::array<T, N> &values)
    {
        std::ostringstream output;
        output << std::hex << std::setfill('0');
        for (std::size_t i = 0; i < values.size(); ++i)
        {
            if (i != 0)
            {
                output << ' ';
            }
            output << "0x";
            if constexpr (sizeof(T) == sizeof(uint32_t))
            {
                output << std::setw(8) << static_cast<uint32_t>(values[i]);
            }
            else
            {
                output << std::setw(16) << static_cast<unsigned long long>(values[i]);
            }
        }
        return output.str();
    }

    template <typename T>
    using StateArray = std::array<T, 8>;

    template <typename T>
    using BlockArray = std::array<T, 16>;

    template <typename T>
    using CompressFunction = StateArray<T> (*)(const StateArray<T> &, const BlockArray<T> &, std::size_t);

    template <typename T>
    StateArray<T> apply_prefix_blocks(const std::map<std::string, std::string> &config,
                                      const StateArray<T> &initial_state,
                                      std::size_t message_count,
                                      std::size_t rounds,
                                      CompressFunction<T> compress)
    {
        StateArray<T> state = initial_state;

        if (message_count == 1)
        {
            return state;
        }

        if (message_count != 2)
        {
            throw std::runtime_error("Unsupported Message_count: " +
                                     std::to_string(message_count));
        }

        const auto msg0 = parse_hex_array<T, 16>(read_field(config, "MSG0"));
        return compress(state, msg0, rounds);
    }

} // namespace

int main(int argc, char *argv[])
{
    try
    {
        if (argc != 2)
        {
            std::cerr << "Usage: " << argv[0] << " <config_file>\n";
            return 1;
        }

        auto config = parse_config(argv[1]);

        const std::string version = normalize_version(read_field(config, "Version"));
        const std::size_t message_count =
            static_cast<std::size_t>(std::stoul(read_field(config, "Message_count")));
        const std::size_t rounds =
            static_cast<std::size_t>(std::stoul(read_field(config, "Round")));
        const std::string type = normalize_type(read_field(config, "Type"));

        if (version == "SHA256")
        {
            const auto msg1 =
                parse_hex_array<uint32_t, 16>(read_field(config, "MSG1"));
            const auto msg2 =
                parse_hex_array<uint32_t, 16>(read_field(config, "MSG2"));
            std::array<uint32_t, 8> iv1{};
            std::array<uint32_t, 8> iv2{};

            if (type == "FREE_START")
            {
                iv1 = parse_hex_array<uint32_t, 8>(read_field(config, "IV1"));
                iv2 = parse_hex_array<uint32_t, 8>(read_field(config, "IV2"));
            }
            else if (type == "SEMI_FREE_START")
            {
                iv1 = parse_hex_array<uint32_t, 8>(read_field(config, "IV"));
                iv2 = iv1;
            }else if (type == "Collision")
            {
                iv1 = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
                iv2 = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
            }

            const auto input_state1 =
                apply_prefix_blocks<uint32_t>(config, iv1, message_count, rounds,
                                              sha256_compress);
            const auto input_state2 =
                apply_prefix_blocks<uint32_t>(config, iv2, message_count, rounds,
                                              sha256_compress);
            const auto state1 = sha256_compress(input_state1, msg1, rounds);
            const auto state2 = sha256_compress(input_state2, msg2, rounds);

            std::cout << "Version: SHA256\n";
            std::cout << "Message_count: " << message_count << '\n';
            std::cout << "Round: " << rounds << '\n';
            if (type == "FREE_START")
            {
                std::cout << "Type: free-start collision verification\n";
            }
            else if (type == "SEMI_FREE_START")
            {
                std::cout << "Type: semi-free-start collision verification\n";
            }
            else if (type == "Collision")
            {
                std::cout << "Type: standard initial value collision verification\n";
            }
            if (type == "FREE_START")
            {
                std::cout << "IV1: " << format_word_array(iv1) << '\n';
                std::cout << "IV2: " << format_word_array(iv2) << '\n';
            }
            else
            {
                std::cout << "IV: " << format_word_array(iv1) << '\n';
            }
            if (message_count == 2)
            {
                const auto msg0 =
                    parse_hex_array<uint32_t, 16>(read_field(config, "MSG0"));
                std::cout << "MSG0: " << format_word_array(msg0) << '\n';
                std::cout << "MSG0 Output for MSG1: " << format_sha256_state(input_state1) << '\n';
                std::cout << "MSG0 Output for MSG2: " << format_sha256_state(input_state2) << '\n';
            }
            std::cout << "MSG1: " << format_word_array(msg1) << '\n';
            std::cout << "MSG2: " << format_word_array(msg2) << '\n';
            std::cout << "MSG1 Hash: " << format_sha256_state(state1) << '\n';
            std::cout << "MSG2 Hash: " << format_sha256_state(state2) << '\n';
            std::cout << "Collision: " << (state1 == state2 ? "YES" : "NO")
                      << '\n';
        }
        else if (version == "SHA512")
        {
            const auto msg1 =
                parse_hex_array<uint64_t, 16>(read_field(config, "MSG1"));
            const auto msg2 =
                parse_hex_array<uint64_t, 16>(read_field(config, "MSG2"));
            std::array<uint64_t, 8> iv1{};
            std::array<uint64_t, 8> iv2{};

            if (type == "FREE_START")
            {
                iv1 = parse_hex_array<uint64_t, 8>(read_field(config, "IV1"));
                iv2 = parse_hex_array<uint64_t, 8>(read_field(config, "IV2"));
            }
            else if (type == "SEMI_FREE_START")
            {
                iv1 = parse_hex_array<uint64_t, 8>(read_field(config, "IV"));
                iv2 = iv1;
            }
            else if (type == "Collision")
            {
                iv1 = {0x6a09e667f3bcc908ULL, 0xbb67ae8584caa73bULL,
                       0x3c6ef372fe94f82bULL, 0xa54ff53a5f1d36f1ULL,
                       0x510e527fade682d1ULL, 0x9b05688c2b3e6c1fULL,
                       0x1f83d9abfb41bd6bULL, 0x5be0cd19137e2179ULL};
                iv2 = {0x6a09e667f3bcc908ULL, 0xbb67ae8584caa73bULL,
                       0x3c6ef372fe94f82bULL, 0xa54ff53a5f1d36f1ULL,
                       0x510e527fade682d1ULL, 0x9b05688c2b3e6c1fULL,
                       0x1f83d9abfb41bd6bULL, 0x5be0cd19137e2179ULL};
            }
            else
            {
                throw std::runtime_error("Unsupported SHA512 Type: " + type);
            }

            const auto input_state1 =
                apply_prefix_blocks<uint64_t>(config, iv1, message_count, rounds,
                                              sha512_compress);
            const auto input_state2 =
                apply_prefix_blocks<uint64_t>(config, iv2, message_count, rounds,
                                              sha512_compress);
            const auto state1 = sha512_compress(input_state1, msg1, rounds);
            const auto state2 = sha512_compress(input_state2, msg2, rounds);

            std::cout << "Version: SHA512\n";
            std::cout << "Message_count: " << message_count << '\n';
            std::cout << "Round: " << rounds << '\n';
            if (type == "FREE_START")
            {
                std::cout << "Type: free-start collision verification\n";
            }
            else if (type == "SEMI_FREE_START")
            {
                std::cout << "Type: semi-free-start collision verification\n";
            }
            else if (type == "Collision")
            {
                std::cout << "Type: standard initial value collision verification\n";
            }
            if (type == "FREE_START")
            {
                std::cout << "IV1: " << format_word_array(iv1) << '\n';
                std::cout << "IV2: " << format_word_array(iv2) << '\n';
            }
            else
            {
                std::cout << "IV: " << format_word_array(iv1) << '\n';
            }
            if (message_count == 2)
            {
                const auto msg0 =
                    parse_hex_array<uint64_t, 16>(read_field(config, "MSG0"));
                std::cout << "MSG0: " << format_word_array(msg0) << '\n';
                std::cout << "MSG0 Output for MSG1: " << format_sha512_state(input_state1) << '\n';
                std::cout << "MSG0 Output for MSG2: " << format_sha512_state(input_state2) << '\n';
            }
            std::cout << "MSG1: " << format_word_array(msg1) << '\n';
            std::cout << "MSG2: " << format_word_array(msg2) << '\n';
            std::cout << "MSG1 Hash: " << format_sha512_state(state1) << '\n';
            std::cout << "MSG2 Hash: " << format_sha512_state(state2) << '\n';
            std::cout << "Collision: " << (state1 == state2 ? "YES" : "NO")
                      << '\n';
        }
        else
        {
            throw std::runtime_error("Unsupported Version: " + version);
        }
    }
    catch (const std::exception &error)
    {
        std::cerr << error.what() << '\n';
        return 1;
    }

    return 0;
}
