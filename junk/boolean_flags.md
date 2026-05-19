## 🔍 Codebase Reality vs. Academic Paper: How the SHA-2 SAT Attack Actually Works

After reverse-engineering the codebase (specifically `find_dc_model_*` and `correct_dc_model_*`), we discovered a significant gap between the theoretical models presented in the paper and the raw implementation. Here is how the cryptographic attack framework actually operates under the hood:

### 1. The "Fast Filtering" Model is a Bypass Switch
The paper describes a "Fast Filtering" model that operates purely in the difference space to keep the SAT solver fast. In the code, **this is not a distinct truth table.** * When the "Full Model" is active (`op = 1`), the solver applies massive 11-variable constraint blocks linking difference bits $(v,d)$ to value monitoring bits.
* When "Fast Filtering" is active (`op = 0`), the script **literally skips the Boolean functions entirely** (no `IF`, `MAJ`, or `XOR` constraints are emitted). It relies entirely on the surrounding modular addition constraints to hold the trail together. 

### 2. `find_dc` (Explorer) vs. `correct_dc` (Patcher)
Because bypassing constraints (`op = 0`) creates mathematically loose trails, the architecture requires two distinct phases:
* **`find_dc`:** The explorer. It skips constraints to run fast, minimizing the Hamming Weight (HW) of active differences to sketch a rough "shape" of a collision.
* **`correct_dc`:** The patcher. It uses hardcoded string arrays to **freeze** the solver to the exact differential path found by `find_dc`. Once pinned, it selectively activates the "Full" value-monitoring constraints (via `op7`) on dense rounds (e.g., rounds 5–7) to force the solver to resolve any hidden contradictions.

### 3. The "Real Messages" Illusion
Despite references to value transitions, **these scripts never generate real 32-bit message blocks ($M$ and $M'$).** Even when `correct_dc` tracks "values", it operates in a localized, 1-bit SAT universe using abstract boolean placeholders. It simply proves that a valid configuration *can* exist. The actual generation of concrete hexadecimal message blocks is delegated to an entirely separate, downstream `collision_verify` script.

### 💡 The Bottom Line
The SAT solver is not fully automated; it is manually piloted. The attackers use `find_dc` to sketch a path, hardcode that path into `correct_dc`, turn on localized value-monitors to check the math, and manually toggle Boolean constraints (`op` flags) on and off to steer the solver's complexity.