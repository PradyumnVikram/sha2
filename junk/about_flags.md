# Analysis of the SHA-256 Differential Attack Strategy

This is a phenomenal mapping of the codebase. By cross-referencing the exact round indices where the flags toggle in your scripts with the equations in the paper, we can decode exactly what the authors' attack strategy is.

The toggling of the flags is not an optimization; it is a literal blueprint of the differential characteristic's shape (the visual blocks in Figure 2 of the paper).

Here is exactly what the flags are doing: The authors divide the state updates for registers A and E into two distinct phases: The Active Cancellation Phase and The Silent Propagation Phase.

## The Two Phases of the Attack

* **Method 2 (flag = 0 / Cancellation Phase):** During the middle steps of the attack, the attacker is injecting differences from the message (W) into the state (A and E). The solver's goal here is to carefully align these differences so they eventually crash into each other and mathematically cancel out to zero (x−y=0).

* **Method 1 (flag = 1 / Propagation Phase):** Once the differences have successfully cancelled out and the state has returned to a difference of zero, the hard work is done. The attacker switches the script to Method 1 (Expansion, z→z′) simply to carry that zero forward for the remaining steps. Since 0 expanding to 0 is trivially valid, this basically tells the solver, "Keep this lane quiet."

Let's prove this by mapping your Python array indices directly to the mathematical constraints defined in the paper.

## Proof 1: The 39-Step SHA-256 Attack

Look at Section 4.1 (Step 2) of the paper. The authors explicitly state the mathematical boundaries for when the state differences must completely vanish:

> "∀i∈[19,38]:δAi = 0" 
> "∀i∈[23,38]:δEi = 0"

Now look at your Python trace for `find_dc_model_39.py`:

* **Register A (op5):** The flag is 0 (Method 2 / Cancellation) for rounds 8–18. Exactly at round 19, it switches to 1 (Method 1 / Silent Propagation). This perfectly matches δAi = 0 at step 19!
* **Register E (op2):** The flag is 0 (Method 2 / Cancellation) for rounds 8–22. Exactly at round 23, it switches to 1 (Method 1 / Silent Propagation). This perfectly matches δEi = 0 at step 23!

## Proof 2: The 31-Step SHA-256 Attack

Look at Section 4.2 (Step 2). The authors establish the boundaries for the 31-step attack:

> "∀i∈[11,30]:δAi = 0" 
> "∀i∈[15,30]:δEi = 0"

Now look at your Python trace for `find_dc_model_31_256.py`:

* **Register A (op5):** Switches from 0 to 1 exactly at round 11.
* **Register E (op2):** Switches from 0 to 1 exactly at round 15.

The arrays you found (op2 and op5) are the literal programmatic translations of the δ=0 boundary conditions written in the paper. The attacker manually hardcodes these arrays to tell the SAT solver exactly when it needs to stop fighting to cancel differences and just let the zeros flow.

## The Mystery of the Message Expansion (op6 vs op8)

You noticed a discrepancy between `find_dc_model_31_256.py` and `correct_dc_model_31_256.py` regarding the message expansion (W).

* `find_dc` uses `op8` (all 0s / Method 2 Cancellation).
* `correct_dc` uses `op6` (all 1s / Method 1 Expansion).

This maps perfectly to the authors' methodology described at the end of Section 4.2. They state:

> "Without this strategy, we found that the obtained differential characteristic was indeed invalid."

Here is what happened in the codebase:

1.  **The First Pass (find_dc):** They ran the solver using `op8 = 0`. By forcing Method 2 (Cancellation) on the message words for steps 16–30, they rigidly constrained the solver to ensure that all message differences collapsed to zero as quickly as possible.
2.  **The Correction Pass (correct_dc):** The characteristic they found in step 1 was invalid (it contained mathematical contradictions). To fix it, they wrote `correct_dc`, where they switch the message expansion to `op6 = 1` (Method 1). Method 1 allows differences to dynamically expand (z→z′). By loosening the rigid cancellation requirements and giving the solver the flexibility of Method 1, combined with the concrete value transitions, the solver was able to shift the bits around to resolve the contradictions without breaking the overall collision shape.

## Conclusion

The flags are the steering wheel for the SAT solver. The authors manually map out the desired shape of the differential characteristic (dense in the middle, zeros on the ends). They feed that map to the Python script via op arrays, flipping the switch from "Cancellation" to "Expansion" at the exact boundaries where they want the state to return to normal.

It is brilliant, highly manual algebraic engineering masquerading as automated solving!