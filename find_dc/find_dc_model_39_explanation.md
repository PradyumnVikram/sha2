# find_dc_model_39.py Explanation

## Purpose
This script assembles and solves a SHA-256 differential characteristic model using STP/CVC.
It encodes one active window of SHA-256 rounds, a message schedule of 39 words, and a selected set of differential message indices.

## Main components

- `FunctionModel` class
  - Encodes the search model parameters and builds constraint lists.
  - `__init__`: sets up the active round window, message bound, and operation flags.
  - `save_variable()`: records unique bitvector declarations.
  - `check_assign()`: ensures all generated variables are declared.
  - `assign_value()`: applies fixed zero conditions for non-differential message words, boundary values for the active window, and a simple weight condition for selected message words.
  - `main()`: calls helper functions from `unit_function_256.py` to build the SHA-256 round constraints for the selected step window and message expansion.
  - `obj_value()`: builds a query that constrains the total Hamming weight of the output differential bits at the final step.
  - `solver()`: writes the combined constraints and declarations to `find_dc_model.cvc`, invokes STP, and checks if the model is satisfiable for descending objective weights.

## How it works

- The model fixes all message words not listed in `message_differential` to zero.
- It uses selected control flags `op0`..`op7` to choose which SHA-256 functions and expansions are active in each round.
- The active window is defined by `start_step` and `end_step`.
- The solver loop lowers the objective from `init_HW` down to 0, finding the smallest feasible Hamming weight solution.
- When a satisfying counterexample is found, the model saves the output and prints the differential characteristic.

## Execution

The script contains a main block that sets:
- `start_step = 8`
- `end_step = 27`
- `message_bound = 39`
- `init_HW = 90`
- `message_differential = [8, 9, 10, 11, 12, 16, 17, 24, 26]`

It then constructs and runs `FunctionModel(...).solver()`.
