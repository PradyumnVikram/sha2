# `unit_function_256.py` Explanation

`unit_function_256.py` contains the reusable SHA-256 constraint-building code
used by the differential-characteristic search scripts. It generates STP bit-vector declarations and
assertions that describe valid SHA-256 difference propagation.

## Signed-Difference Representation

The code represents each bit difference with two one-bit variables `(v, d)`.
The `d` bit records whether a difference exists, and the `v` bit records the
direction of that difference.
`=` means no difference, encoded as `(0, 0)` or `(1, 0)`.
`n` means a downward signed difference, encoded as `(0, 1)`.
`u` means an upward signed difference, encoded as `(1, 1)`.

Common variable prefixes:

- `xv`, `xd`: A-register SHA-256 state differences.
- `yv`, `yd`: E-register SHA-256 state differences.
- `wv`, `wd`: message schedule word differences.
- `cv`, `cd`: carry differences for round additions.
- `mcv`, `mcd`: carry differences for message expansion.

## Main Functions

`generate_constraints` converts invalid transition rows from
`constrain_condition.py` into STP assertions.

`addition_function` models modular addition of signed differences. 

`expand_model` connects modular differences with signed-difference patterns.
It lets the solver explore signed trails that are compatible with the same
modular difference. The `flag` argument chooses which expansion is used.
When `flag == 1`, the model expands a signed difference directly. Otherwise,
it uses a rearranged version of the same relation, corresponding to a
subtraction-style view of the expansion.

`xor_function`, `if_function`, and `maj_function` model SHA-256 boolean
operations at the signed-difference level.

`sha_e` builds constraints for the E-register state update. It combines the
E-register sigma function, the choose function, message word differences, and
modular additions. `__op0` enables the Sigma1 model, `__op1` enables the MAJ function model and `__op2` selects the expansion mode.

`sha_a` builds constraints for the A-register state update. It combines the
A-register sigma function, the majority function, and modular additions. `__op3` enables the Sigma0 model, `__op4` 
enables the MAJ function model and `__op5` selects the expansion mode.

Both `sha_e` and `sha_a` return two lists: STP variable declarations and STP assertion
strings. The model script later collects these into one `.cvc` solver input
file.

`message_expand` models SHA-256 message schedule expansion. Logical shifts are
modeled by appending temporary variables constrained to zero.

`sha2_value` adds concrete bit-value constraints for one SHA-256 step, including the round
constant. These constraints help verify that a signed-difference trail can
correspond to actual SHA-256 state values.

`get_dc` parses STP solver output for one variable family, such as `x`, `y`,
or `w`. It reads the solver assignments, reconstructs the `v` and `d` arrays for each
bit, and converts them into readable symbols (u, = , n). It then prints each word from the most significant bit to the least significant
bit.

`read_differential_characteristic` is the top-level output parser. It reads a saved STP counterexample file and extracts the three main trail 
families: `x`, which represents the A-register state trail; `y`, which represents the E-register state trail; and `w`, 
which represents the message schedule trail. It calls `get_dc` for each family and returns the formatted differential characteristic for printing.
