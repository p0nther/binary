To reverse engineer decompiled C code independently, follow a structured 4-step framework.

---

### Phase 1: Locate the Entry & Control Flow

Start at `main` or the function controlling execution logic.

* **Identify Key Actions:** Scan from top to bottom. Look for input/output functions (`read`, `recv`, `scanf`, `malloc`), system calls (`open`), and conditional checks (`if`, `memcmp`, `assert`).
* **Trace Structural Anchors:** Notice how `/challenge/.key` is opened and read into memory (`local_38`). That identifies `local_38` as the cryptographic key variable.

---

### Phase 2: Map the Stack Layout

Decompilers assign variable names based on stack offsets (e.g., `local_58` means `RBP - 0x58`).

1. **Find Variable Offsets:** Look at the variable declarations:
* `local_68` $\rightarrow$ Offset `-0x68`
* `local_60` $\rightarrow$ Offset `-0x60`
* `local_58` $\rightarrow$ Offset `-0x58`


2. **Calculate Distance & Buffers:**
* Distance from `local_68` to `local_60`: $0\text{x}68 - 0\text{x}60 = 0\text{x}8$ (8 bytes).
* Distance from `local_58` to Saved RBP: $0\text{x}58 = 88$ bytes.
* Distance to Return Address: $88 + 8 = 96$ bytes.



---

### Phase 3: Trace Input vs. Operations

Follow what happens to user input (`read(0, local_18, 0x1000)`):

1. **Track Destination & Size:** User input goes to heap buffer `local_18` (up to `0x1000` bytes).
2. **Analyze Constraints:**
* `(local_20 & 0xf) != 0` $\rightarrow$ Check $N \bmod 16 \neq 0$ (Block alignment rule).


3. **Analyze Operations:**
* `EVP_DecryptUpdate(..., local_68, ..., local_18, 0x10)` $\rightarrow$ Decrypts first 16 bytes into `local_68`.
* `EVP_DecryptUpdate(..., local_58, ..., local_18 + 0x10, local_20 - 0x10)` $\rightarrow$ Decrypts remaining input into `local_58` (32-byte stack array).



---

### Phase 4: Identify Logic Flaws & Vulnerabilities

Compare **Checks** against **Operations**:

* **Check:** `local_60` is validated to be $\le 16$.
* **Operation:** Does the second decryption use `local_60` to limit written bytes? **No.** It writes `local_20 - 0x10` bytes into `local_58`.
* **Conclusion:** If `local_20` (input length) exceeds 32 bytes, a stack buffer overflow occurs.

---

### Essential Technical Reference & Manual Search Queries

When encountering unfamiliar functions, look up specific terms using targeted search queries:

* **OpenSSL API Mechanics:** Search `man EVP_DecryptInit_ex` or `EVP_aes_128_ecb documentation` to understand cipher mode, key sizes, and block sizes.
* **Ghidra Data Types:** Search `Ghidra undefined4 size` or `Ghidra stack offset interpretation` to quickly map local variables.
* **Bitwise Constraints:** Search `python bitwise AND alignment check` to analyze operations like `(len & 0xf) != 0`.
