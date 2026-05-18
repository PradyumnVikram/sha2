#ifndef CHECK_VALUE_HASH_UTILS_H
#define CHECK_VALUE_HASH_UTILS_H

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string>

namespace check_value {

inline constexpr std::array<uint32_t, 64> kSha256Constants = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1,
    0x923f82a4, 0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147,
    0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
    0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

inline constexpr std::array<uint64_t, 80> kSha512Constants = {
    0x428a2f98d728ae22ULL, 0x7137449123ef65cdULL, 0xb5c0fbcfec4d3b2fULL,
    0xe9b5dba58189dbbcULL, 0x3956c25bf348b538ULL, 0x59f111f1b605d019ULL,
    0x923f82a4af194f9bULL, 0xab1c5ed5da6d8118ULL, 0xd807aa98a3030242ULL,
    0x12835b0145706fbeULL, 0x243185be4ee4b28cULL, 0x550c7dc3d5ffb4e2ULL,
    0x72be5d74f27b896fULL, 0x80deb1fe3b1696b1ULL, 0x9bdc06a725c71235ULL,
    0xc19bf174cf692694ULL, 0xe49b69c19ef14ad2ULL, 0xefbe4786384f25e3ULL,
    0x0fc19dc68b8cd5b5ULL, 0x240ca1cc77ac9c65ULL, 0x2de92c6f592b0275ULL,
    0x4a7484aa6ea6e483ULL, 0x5cb0a9dcbd41fbd4ULL, 0x76f988da831153b5ULL,
    0x983e5152ee66dfabULL, 0xa831c66d2db43210ULL, 0xb00327c898fb213fULL,
    0xbf597fc7beef0ee4ULL, 0xc6e00bf33da88fc2ULL, 0xd5a79147930aa725ULL,
    0x06ca6351e003826fULL, 0x142929670a0e6e70ULL, 0x27b70a8546d22ffcULL,
    0x2e1b21385c26c926ULL, 0x4d2c6dfc5ac42aedULL, 0x53380d139d95b3dfULL,
    0x650a73548baf63deULL, 0x766a0abb3c77b2a8ULL, 0x81c2c92e47edaee6ULL,
    0x92722c851482353bULL, 0xa2bfe8a14cf10364ULL, 0xa81a664bbc423001ULL,
    0xc24b8b70d0f89791ULL, 0xc76c51a30654be30ULL, 0xd192e819d6ef5218ULL,
    0xd69906245565a910ULL, 0xf40e35855771202aULL, 0x106aa07032bbd1b8ULL,
    0x19a4c116b8d2d0c8ULL, 0x1e376c085141ab53ULL, 0x2748774cdf8eeb99ULL,
    0x34b0bcb5e19b48a8ULL, 0x391c0cb3c5c95a63ULL, 0x4ed8aa4ae3418acbULL,
    0x5b9cca4f7763e373ULL, 0x682e6ff3d6b2b8a3ULL, 0x748f82ee5defb2fcULL,
    0x78a5636f43172f60ULL, 0x84c87814a1f0ab72ULL, 0x8cc702081a6439ecULL,
    0x90befffa23631e28ULL, 0xa4506cebde82bde9ULL, 0xbef9a3f7b2c67915ULL,
    0xc67178f2e372532bULL, 0xca273eceea26619cULL, 0xd186b8c721c0c207ULL,
    0xeada7dd6cde0eb1eULL, 0xf57d4f7fee6ed178ULL, 0x06f067aa72176fbaULL,
    0x0a637dc5a2c898a6ULL, 0x113f9804bef90daeULL, 0x1b710b35131c471bULL,
    0x28db77f523047d84ULL, 0x32caab7b40c72493ULL, 0x3c9ebe0a15c9bebcULL,
    0x431d67c49c100d4cULL, 0x4cc5d4becb3e42b6ULL, 0x597f299cfc657e2aULL,
    0x5fcb6fab3ad6faecULL, 0x6c44198c4a475817ULL};

inline uint32_t rotr32(uint32_t value, uint32_t bits) {
  return (value >> bits) | (value << (32 - bits));
}

inline uint64_t rotr64(uint64_t value, uint64_t bits) {
  return (value >> bits) | (value << (64 - bits));
}

inline uint32_t ch32(uint32_t x, uint32_t y, uint32_t z) {
  return (x & y) ^ (~x & z);
}

inline uint64_t ch64(uint64_t x, uint64_t y, uint64_t z) {
  return (x & y) ^ (~x & z);
}

inline uint32_t maj32(uint32_t x, uint32_t y, uint32_t z) {
  return (x & y) ^ (x & z) ^ (y & z);
}

inline uint64_t maj64(uint64_t x, uint64_t y, uint64_t z) {
  return (x & y) ^ (x & z) ^ (y & z);
}

inline uint32_t big_sigma0_32(uint32_t x) {
  return rotr32(x, 2) ^ rotr32(x, 13) ^ rotr32(x, 22);
}

inline uint32_t big_sigma1_32(uint32_t x) {
  return rotr32(x, 6) ^ rotr32(x, 11) ^ rotr32(x, 25);
}

inline uint32_t small_sigma0_32(uint32_t x) {
  return rotr32(x, 7) ^ rotr32(x, 18) ^ (x >> 3);
}

inline uint32_t small_sigma1_32(uint32_t x) {
  return rotr32(x, 17) ^ rotr32(x, 19) ^ (x >> 10);
}

inline uint64_t big_sigma0_64(uint64_t x) {
  return rotr64(x, 28) ^ rotr64(x, 34) ^ rotr64(x, 39);
}

inline uint64_t big_sigma1_64(uint64_t x) {
  return rotr64(x, 14) ^ rotr64(x, 18) ^ rotr64(x, 41);
}

inline uint64_t small_sigma0_64(uint64_t x) {
  return rotr64(x, 1) ^ rotr64(x, 8) ^ (x >> 7);
}

inline uint64_t small_sigma1_64(uint64_t x) {
  return rotr64(x, 19) ^ rotr64(x, 61) ^ (x >> 6);
}

inline std::array<uint32_t, 8> sha256_compress(
    const std::array<uint32_t, 8>& iv,
    const std::array<uint32_t, 16>& block,
    std::size_t rounds = 64) {
  rounds = std::min(rounds, kSha256Constants.size());

  std::array<uint32_t, 64> w{};
  for (std::size_t i = 0; i < block.size(); ++i) {
    w[i] = block[i];
  }
  for (std::size_t i = 16; i < w.size(); ++i) {
    w[i] = small_sigma1_32(w[i - 2]) + w[i - 7] + small_sigma0_32(w[i - 15]) +
           w[i - 16];
  }

  uint32_t a = iv[0];
  uint32_t b = iv[1];
  uint32_t c = iv[2];
  uint32_t d = iv[3];
  uint32_t e = iv[4];
  uint32_t f = iv[5];
  uint32_t g = iv[6];
  uint32_t h = iv[7];

  for (std::size_t i = 0; i < rounds; ++i) {
    const uint32_t t1 =
        h + big_sigma1_32(e) + ch32(e, f, g) + kSha256Constants[i] + w[i];
    const uint32_t t2 = big_sigma0_32(a) + maj32(a, b, c);
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

inline std::array<uint64_t, 8> sha512_compress(
    const std::array<uint64_t, 8>& iv,
    const std::array<uint64_t, 16>& block,
    std::size_t rounds = 80) {
  rounds = std::min(rounds, kSha512Constants.size());

  std::array<uint64_t, 80> w{};
  for (std::size_t i = 0; i < block.size(); ++i) {
    w[i] = block[i];
  }
  for (std::size_t i = 16; i < w.size(); ++i) {
    w[i] = small_sigma1_64(w[i - 2]) + w[i - 7] + small_sigma0_64(w[i - 15]) +
           w[i - 16];
  }

  uint64_t a = iv[0];
  uint64_t b = iv[1];
  uint64_t c = iv[2];
  uint64_t d = iv[3];
  uint64_t e = iv[4];
  uint64_t f = iv[5];
  uint64_t g = iv[6];
  uint64_t h = iv[7];

  for (std::size_t i = 0; i < rounds; ++i) {
    const uint64_t t1 =
        h + big_sigma1_64(e) + ch64(e, f, g) + kSha512Constants[i] + w[i];
    const uint64_t t2 = big_sigma0_64(a) + maj64(a, b, c);
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

inline std::string format_sha256_state(const std::array<uint32_t, 8>& state) {
  std::ostringstream output;
  output << std::hex << std::setfill('0');
  for (std::size_t i = 0; i < state.size(); ++i) {
    if (i != 0) {
      output << ' ';
    }
    output << std::setw(8) << state[i];
  }
  return output.str();
}

inline std::string format_sha512_state(const std::array<uint64_t, 8>& state) {
  std::ostringstream output;
  output << std::hex << std::setfill('0');
  for (std::size_t i = 0; i < state.size(); ++i) {
    if (i != 0) {
      output << ' ';
    }
    output << std::setw(16) << state[i];
  }
  return output.str();
}

}  // namespace check_value

using check_value::format_sha256_state;
using check_value::format_sha512_state;
using check_value::sha256_compress;
using check_value::sha512_compress;

#endif
