# verify_result User Manual

## 1. Overview

`verify_result` is a command-line verification tool for reduced-round SHA-256 and SHA-512 compression results.

The program reads a configuration file, applies the selected verification mode, computes the hash states for two candidate message blocks, and reports whether the two outputs collide.

## 2. Supported Features

- SHA-256 verification
- SHA-512 verification
- Free-start collision verification
- Semi-free-start collision verification
- Standard initial-value collision verification
- One-block and two-block message chaining controlled by `Message_count`

## 3. Build Instructions

Open a terminal in the `verify_result` directory and compile the program with:

```bash
g++ -std=c++17 main.cpp -o check_value
```

## 4. Run Instructions

Run the executable with a configuration file:

```bash
./check_value <config_file>
```

If no configuration file is provided, the program prints:

```text
Usage: ./check_value <config_file>
```

## 5. Configuration File Format

The configuration file uses the format:

```text
key: value;
```

Each field must appear on its own line.

Example:

```text
Message_count: 2;
Version: SHA256;
Round: 31;
Type: Collision;
MSG0: 0x8ce3f805,0x5c401aed,0x579e5f7f,0xbc3116cb,0xca189b3c,0xeb75f04c,0x958f0a0e,0x7760b082,0xdcd5027d,0x32260ad6,0x7b12b659,0xeee66518,0xad7f88dd,0xf8ad20bb,0x7ae40ffd,0x21609249;
MSG1: 0x9abdeb1b,0x1f195f41,0x5a7210c1,0x55614f13,0xa2269dd1,0xbe888a61,0x359257d4,0xadf3737b,0x9f0484a6,0xeb830a58,0x66add94a,0x9669232d,0x45271fa5,0xb8f69585,0x428bbce3,0x0703b904;
MSG2: 0x9abdeb1b,0x1f195f41,0x5a7210c1,0x55614f13,0xa2269dd1,0xbe887a67,0x35b2dfc5,0xfde32975,0xc70595a6,0xeb838a5c,0x66add94a,0x9669232d,0x45271fa5,0xb8f69585,0x428bbce3,0x0703b904;
```

## 6. Parameter Reference

### `Message_count`

Specifies how many message stages are used in the verification process.

Currently supported values:

- `1`
- `2`

### `Version`

Selects the hash function.

Allowed values:

- `SHA256`
- `SHA512`

### `Round`

Specifies the number of compression rounds to execute.

### `Type`

Selects the verification mode.

Accepted forms:

- `FS`
- `FREE_START`
- `FREE-START`
- `SFS`
- `SEMI_FREE_START`
- `SEMI-FREE-START`
- `Collision`

### `IV`

Required for semi-free-start verification.

### `IV1`, `IV2`

Required for free-start verification.

### `MSG0`

Required when `Message_count` is `2`.

### `MSG1`, `MSG2`

Always required.

## 7. Verification Modes

### 7.1 Free-Start Verification

When `Type` is `FREE_START`, the program:

- reads `IV1`
- reads `IV2`
- compresses `MSG1` from `IV1`
- compresses `MSG2` from `IV2`

### 7.2 Semi-Free-Start Verification

When `Type` is `SEMI_FREE_START`, the program:

- reads `IV`
- uses the same initial value for both message paths
- compresses `MSG1` and `MSG2` from that shared initial value

### 7.3 Standard Initial-Value Collision Verification

When `Type` is `Collision`, the program uses the built-in standard initial values:

- SHA-256 standard IV for `SHA256`
- SHA-512 standard IV for `SHA512`

No external `IV`, `IV1`, or `IV2` fields are required in this mode.

## 8. Message_count Behavior

### 8.1 `Message_count: 1`

The program directly computes:

```text
initial state -> MSG1
initial state -> MSG2
```

### 8.2 `Message_count: 2`

The program first compresses `MSG0`, then uses the output of `MSG0` as the input state for both `MSG1` and `MSG2`.

Flow:

```text
initial state -> MSG0 -> intermediate state -> MSG1
initial state -> MSG0 -> intermediate state -> MSG2
```

In this mode, the output of `MSG0` is printed so you can inspect the intermediate chaining state.

## 9. Output Description

The program prints:

- hash version
- message count
- round count
- verification type
- initial value or values
- `MSG0` and its intermediate state when `Message_count` is `2`
- `MSG1`
- `MSG2`
- final hash state of `MSG1`
- final hash state of `MSG2`
- collision result

The final collision result is shown as:

- `Collision: YES`
- `Collision: NO`

## 10. Data Requirements

- Each message block must contain exactly 16 words.
- Each SHA state must contain exactly 8 words.
- All values must be written in hexadecimal form.
- The program currently supports only `Message_count = 1` and `Message_count = 2`.

## 11. Common Errors

Typical errors include:

- missing fields in the configuration file
- unsupported `Version`
- unsupported `Type`
- unsupported `Message_count`
- incorrect number of message words
- incorrect number of IV words

## 12. Example Workflow

1. Edit `msg.txt`.
2. Set `Message_count`, `Version`, `Round`, and `Type`.
3. Fill in `IV`, `IV1`, `IV2`, `MSG0`, `MSG1`, and `MSG2` as required by the selected mode.
4. Compile the program.
5. Run the executable with the configuration file.
6. Check the printed outputs and the final collision result.
