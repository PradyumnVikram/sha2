# SAT Solver

A SAT Solver is just a Boolean Satisfiability Solver, which takes in a formula in the CNF (Conjunctive Normal Form) and outputs whether a given set of values of the boolean variables in the formula can satisfy it.

CNF → Product of sums, or an AND of OR s. NOT operator can also be used in this. Every [propositional](https://en.wikipedia.org/wiki/Propositional_formula) formula can be converted to its CNF form. In the SAT solvers being used, the syntax to represent our formula in CNF form is the [extended](https://www.msoos.org/xor-clauses/) [DIMACS CNF](https://jix.github.io/varisat/manual/0.2.0/formats/dimacs.html).

[CryptoMiniSat SAT Solver](https://github.com/msoos/cryptominisat) in particular uses the CNF with extend XOR clauses, as mentioned in the reference to “extended”. The form is as follows:

```
p cnf 3 2
1 2 -3 0
-2 3 0
```

- The first line is of the form `p cnf <variables> <clauses>`, that is the first argument represents the number of variables, and the second argument represents the number of clauses. 
- A clause is anything that starts after the initial `p cnf <variables> <clauses>` till the first 0 is hit.  The `0` at the end is just the delimiter signifying end of clause.
	- If there are $n$ variables, then they are indexed as $1,2, … , n$, thus $v_1, v_2, …, v_n$. 
	- A negative sign in front of the number implies _negation_ of that variable. Thus, `1 2 -3` maps to $v_1 \vee v_2 \vee \neg v_3$. 
	- In the extended version, lines starting with `x`, such as `x 1 2 3 0` represent the XOR operation instead of OR. Thus, it corresponds to $v_1 \oplus v_2 \oplus v_3$, where $\oplus$ is XOR. 
- All the clauses have to evaluate to `1` or True (and hence their AND together) for some input values to the $n$ variables for satisfiability to exist. 

It seems SAT solvers use stuff like [Boolean Constraint Propagation](https://en.wikipedia.org/wiki/Unit_propagation) to simply the CNF further? 

https://haz-tech.blogspot.com/2010/08/whos-watching-watch-literals.html?m=1

---

# STP and the `.cvc` Files

The `find_dc` scripts do not feed DIMACS CNF directly. They build a text file (conventionally `find_dc_model.cvc`) in the **CVC language** understood by [STP](https://stp.github.io/) — a bit-vector SMT solver. STP can translate that file internally and hand it to a SAT backend. In this repo the backend is **CryptoMiniSat**, invoked like this:

```
stp find_dc_model.cvc --cryptominisat --threads 26
```

So the pipeline is: Python strings → `.cvc` file → STP → CryptoMiniSat → `Valid.` or a counterexample.

## Declarations

Every bit in the differential model is its own 1-bit variable:

```
xd_8_31: BITVECTOR(1);
yd_12_0: BITVECTOR(1);
```

The Python helper `save_variable("xd_8_31")` just appends that declaration line once. There is no 32-bit word type at the STP layer — a whole SHA word is 32 (or 64) separate `BITVECTOR(1)` wires.

## Assertions

Constraints are plain equalities and bit-vector operations prefixed with `ASSERT`:

```
ASSERT xd_8_31 = 0bin0;
ASSERT (yd_13_4 | yd_14_4) = flag_4;
```

- `0bin0` / `0bin1` — binary literals (like writing `0b0` / `0b1`).
- `0bin0000000100` — a wider constant; used when comparing Hamming-weight sums.

The notation `0b0` in comments in the Python files is the same idea as `0bin0` in the generated file.

## Hamming weight in STP

To count how many difference-bits are set, the scripts zero-extend each 1-bit wire to 10 bits and sum:

```
ASSERT BVGT(BVPLUS(10, 0bin000000000@yd_12_0, 0bin000000000@yd_12_1, ...), 0bin0000000001);
```

- `BVPLUS(10, ...)` — add bit-vectors using a 10-bit accumulator so summing up to 64 bits does not overflow the counter.
- `BVGT(A, B)` — strict greater-than on bit-vectors.
- `BVLE(A, B)` — less-than or equal.
- `@` — concatenation. `0bin000000000@yd_12_0` pads the single bit to 10 bits before adding.

This pattern appears everywhere the code “minimizes Hamming weight” or enforces “exactly 4 differences on this round”.

## QUERY and counterexamples

An STP file has two logical parts:

1. **ASSERT block** — everything that must hold (SHA round equations, fixed differences, shape constraints, optional HW bound).
2. **QUERY** — what you ask the solver about.

The scripts always end with:

```
QUERY FALSE;
COUNTEREXAMPLE;
```

Roughly: “Is the conjunction of all ASSERTs unsatisfiable?” If the answer is **not** `Valid.`, STP found a **counterexample** — a concrete assignment to the bit variables that satisfies the model. That assignment is written to `res2_dc_solution_<hw>.out`.

The descending loop in `solver()` works by appending one more ASSERT that fixes the HW objective (via `obj_value()`), then re-running STP until the formula becomes unsat; the last satisfiable HW is kept.

## What you see in the output

Counterexample lines look like:

```
ASSERT( xd_8_31 = 0bin0 );
ASSERT( yd_12_4 = 0bin1 );
```

`read_differential_characteristic()` in `unit_function_256.py` / `unit_function_512.py` parses these lines, pairs `(v, d)` bits, and prints paper-style `=`, `u`, `n` strings.

---

See `FIND_DC.md` for how those variables map to SHA-2 state and how each attack script uses them.