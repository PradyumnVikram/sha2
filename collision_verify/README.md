# collision_verify

Clean-room implementation of the **`verify_result`** tool from `2024_attack_code`: it checks whether two message paths produce the **same chaining state** after **reduced-round** SHA-256 or SHA-512 compression, under **free-start**, **semi-free-start**, or **standard IV** collision models.

## Features

- **SHA-256** and **SHA-512** compression (same arithmetic as FIPS 180-4).
- **Configurable round count** (clamped to the schedule length: 64 / 80).
- **Verification modes**: free-start (`IV1` / `IV2`), semi-free-start (`IV`), standard IV (`Type: Collision`).
- **One or two block pipelines**: `Message_count` 1 or 2 (optional shared `MSG0` prefix).

## Configuration file

Field syntax matches the legacy verifier:

```text
key: value;
```

See `2024_attack_code/README.md` for the full parameter reference; **this program accepts the same config files**.

## Build

```bash
cd collision_verify
cmake -S . -B build
cmake --build build
```

The executable is `build/collision_verify`.

## Run

```bash
./build/collision_verify /path/to/config.txt
```

Exit status is **0** on success (including when `Collision: NO`), **1** on usage or parse/compute errors.

## Project layout

| Path | Purpose |
|------|---------|
| `include/sha2/constants.hpp` | Round constants `K` and standard IVs |
| `include/sha2/compress.hpp` | Single-block compression primitives |
| `include/sha2/format.hpp` | Hex formatting for reports |
| `include/sha2/config.hpp` | Config parsing and validated `ParsedConfig` |
| `include/sha2/verifier.hpp` | Orchestration and report output |
| `src/main.cpp` | Thin CLI wrapper |

## Relationship to `verify_result`

Behavior and textual output are intended to match the original **`check_value`** binary so existing `.txt` configs remain valid. The implementation is reorganized for clarity, documentation, and separation of concerns—not for algorithmic novelty.
