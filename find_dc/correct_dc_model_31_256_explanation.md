# correct_dc_model_31_256.py Explanation

## Purpose
This script constructs a corrected SHA-256 differential characteristic model for a 31-message-word schedule and solves it with STP.
It encodes selective message differentials, fixed boundary conditions, and SHA-256 round function behavior to validate a candidate characteristic.

## Main components

- `FunctionModel` class
  - `__init__`: stores model parameters, active window bounds, and SHA operation flags.
  - `save_variable()`: creates unique bitvector declarations for variables used by the model.
  - `check_assign()`: ensures helper-generated variable names are recorded.
  - `assign_value()`: applies explicit zero constraints to non-differential message words and sets special differential weight constraints for chosen message indices.
  - `main()`: builds round constraints with `sha_e`, `sha_a`, and optional `sha2_value` helper functions to model state updates and differential propagation.
  - `obj_value()`: encodes the target Hamming weight for the final output differential bits.
  - `solver()`: assembles the CVC file, calls STP, and searches downward from the starting objective until a solution is found.

## How it works

- Non-differential message words are fixed to zero, while selected message indices are allowed to carry a differential.
- The model uses per-round flags to control the SHA-256 functions used in each step.
- Additional constraints implement a specific corrected characteristic pattern and boundary conditions for the active window.
- A solver loop tests the existence of a solution for descending Hamming-weight objectives.

## Execution

The script is configured with:
- `start_step = 5`
- `end_step = 19`
- `message_bound = 31`
- `init_HW = 60`
- `message_differential = [5, 6, 7, 8, 9, 16, 18]`

It then runs `FunctionModel(...).solver()` to generate and solve the model.
