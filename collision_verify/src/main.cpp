/**
 * @file main.cpp
 * @brief CLI entry point for reduced-round SHA-256 / SHA-512 collision verification.
 *
 * Reads a configuration file describing IV mode, round count, and message block(s),
 * then reports whether two compression paths yield identical chaining outputs.
 */

#include "sha2/config.hpp"
#include "sha2/verifier.hpp"

#include <iostream>

int main(int argc, char *argv[])
{
    if (argc != 2)
    {
        std::cerr << "Usage: " << (argc > 0 ? argv[0] : "collision_verify")
                  << " <config_file>\n";
        return 1;
    }

    try
    {
        const sha2::ParsedConfig cfg = sha2::parse_config_file(argv[1]);
        return sha2::run_verification(std::cout, std::cerr, cfg);
    }
    catch (const std::exception &error)
    {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
