# Paper Documentation 

A differential characteristic measures how differences between two parallel states evolve from one round to the next round.

In the paper, $x$ is a n-bit word. SHA2 operates on 32-bit or 64-bit words, and thus here $n$ can be 32 or 64.
### SHA2 Hashing Algorithm 
1. Preprocess the message, by padding it. That is, add the merkle-damgard padding, with $10^* || \text{message length}$, where $\text{message length}$ is in the same n bit word. Thus, we get blocks of 512/1024 bits each.
2. A initial hash state is initialized (this is the IV). The hash itself is of 8 words. We can divide the words into $A_0,A_1,A_2,A_3$ and $E_0, E_1, E_2, E_3$ due to how transitions occur inside them (read, $i-1,i,i+1,i+2$ $\to$ $i,i+1,i+2,$$i+3$).   
3. The algorithm runs on every single single message block. Each message block has 16 words for SHA2. For each message block the following happens.
	- Message Expansion: 16 words to $r$ words, where $r$ is the number of rounds. 
		- In each of the $r$ rounds, the previous hash state is updated according to the state transition function, and the new state is related as we mentioned in the Step 2. 

The final state is obtained after all the message blocks have been passed through the algorithm. 

The round function itself just has modular addition ($\boxplus$), XOR ($\oplus$), boolean functions (AND), and circular bit shifts. Modular addition is a non-linear operation, but the rest are linear (since the carry can ripple throughout).

Since the state of the hash function can be represented entirely in terms of $A_i, E_i$, since at round $r$, we have the state as 
$$h= (A_{r},A_{r-1},A_{r-2},A_{r-3},E_{r},E_{r-1},E_{r-2},E_{r-3})$$
where the $A_0, A_{-1},A_{-2},A_{-3}$ and $E_0, E_{-1},E_{-2},E_{-3}$ give you the IV (Initialization Vector), and the state keeps moving this way. Changing these values would give you either the SFS (if difference in only one), FS (if difference in both). 

#### Differential Characteristic
A general cryptanalysis definition of differential characteristic is the round by round evolution of the state difference between the two parallel executions of the cipher/hash function initiated by injecting a specific difference in the messages of the executions. It essentially states that the difference in the final states holds with this probability for this specific differential trail.

The Hash keeps shifting between modular additions and XOR differences.
- $\delta x$ → the standard mathematical difference calculated modulo $2^n$ calculated as $x' - x \pmod{2^n}$.
- $\Delta x$ → array of symbols signifying the change in the state itself. 
	- $n$: The bit went down ($x[i] = 1$, but $x'[i] = 0$).
	- **$u$**: The bit went up ($x[i] = 0$, but $x'[i] = 1$).
	- $0$ or $1$ (often written as $=$) The bit didn't change. ($x[i] = x'[i]$).
	
Wherever 0 or 1 has been used explicitly instead of $=$ it means we require that specific value in that bit.

Each modular difference maps to multiple different XOR differences, thus the number of trails increases. 
$$ \Delta^+ \equiv \sum_{i=0}^{n-1} (\Delta^\pm_i) \cdot 2^i \pmod{2^n} $$
Signed Differences can be represented as bit-vectors, i.e. vectors with elements in the set $\{-1,0,1\}$.

$(v, d)$, the bit $v$ represents value, and bit $d$ represents difference. Specifically, $(0,0)$ and $(1,0)$ means no difference (since $d =0$) $[=]$, $(0,1)$ means $n$ (bit went from 0 to 1), and $(1,1)$ means $u$ (bit went from 1 to 0). For signed difference $\Delta x$, $\Delta x [i] = (x_v[i], x_d[i])$.

> Every “bit” of the signed difference should be thought of as $(v,d)$, i.e. two bits not one. 

(Aside Start)
You can’t apply a general signed difference on any word $m$, it can lead to contradictions (such as word is $0$ in bit $i$, but the signed difference requires it to go from $1$ to $0$).  Given a signed difference, the signed difference after a specific operation (such as XOR, addition etc) can be obtained. In case of bit-by-bit operators such as XOR, there are no issues, since there’s no inter-dependence between individual bits inside a word. However, in modular addition, there’s a potential carry after every bit operation. 
(Aside End)
#### Modular Addition
 For now, the actual messages themselves do not matter to us. We only care about the signed differences (to build the characteristic). In modular addition, since there’s carry operations happening, we need to introduce an intermediate state which can track the index-by-index carry. No carry initially, hence $\Delta c[0] = [=]$. $\Delta c$ is simply an intermediate state during addition of two signed differences, and is influenced solely by the signed differences themselves.
$$(\Delta x[i], \Delta y[i], \Delta c[i]) \to (\Delta z[i], \Delta c[i+1])$$
#### Modular Difference Expansions 
This signed difference obtained corresponds to a given modular difference, and since as long as the modular difference remains the same, the modular addition result can be considered valid (since each of the signed differences, by definition correspond to the same modular difference in decimal value between the two instances, since the operation being done is modular addition we only care about the difference in values to be the same). To explore multiple pathways (since many contradictions arise in SHA2), we explore all the different signed differences possible. 

> $\Delta c$ here is independent of $\Delta c$ in modular addition

- **Method 1** $(\Delta z[i], \Delta c [i]) \to (\Delta \xi [i], \Delta c[i+1])$: Some inputs have two outputs such as `[n= -> n=], [n= -> un]`. These have different carry bits, and this divergent behavior helps explode the number of expansions for a given signed difference since the change in $\Delta c[i+1]$ leads to avalanche effect in the word. Used to model the signed differences.

- **Method 2**: $( \Delta z[i], \Delta \xi[i],\Delta c[i]) \to (\Delta c[i+1])$ [1] Essentially the same thing but used to model something else. This is used to model the signed differences being the same. It seems like there’s no specific need to use this method, since the constraints mentioned in the `constraint_condition.py` file for both the methods, are exactly the same with columns rearranged. 

> It seems like creating two constraint arrays is completely unnecessary? I mean the end result is exactly the same, even according to the flag switching thing. Refer to `expand_model` function in `unit_function_256.py`. 

**Usage of `10` vs `00`.** It appears `10` is being used to end the search if a state of `10` is reached in any of the variables. Each of the arrays present in the code have additional values of the form `--10----`, where $k$ variable constraints have $k$ of these extra terms. The constraints mentioned in the configuration files are not constraints which are to be “matched”, but rather constraints which are supposed to be "banned". If the given state is reached, then backtracking will occur. They act as boolean filters. 

#### Boolean Function Expansions
Boolean functions also have to be modeled in a similar fashion, except there’s the interesting part about Fast-Filtering methods not keeping in mind that there might not exist concrete bits satisfying the given constraints, whereas the full-model explicitly also includes the concrete bits, thus guarantees  

## Errata
[1] → The order mentioned in the paper is not correct, the mentioned column order is $( \Delta \xi[i],\Delta z[i], \Delta c[i]) \to (\Delta c[i+1])$, whereas the correct column order matching the code is $(\Delta z[i], \Delta \xi[i],\Delta c[i]) \to (\Delta c[i+1])$.

Verification: $\Delta z [i] + \Delta c[i] = \Delta \xi [i] + 2 \Delta c[i+1]$ should hold (taking $n = 1$, $u=-1$ and $=$ = 0). This does not hold for the Table 3, Method 2 values provided.


