# Buffer Overflow → Saved RIP Overwrite → Control Flow Hijacking → ret2win

When many beginners first encounter Buffer Overflow, they immediately start memorizing payloads like:

```text
"A" * 72 + win_address
```

and try random offsets until the program crashes.

But without understanding **how the stack works**, why the **Saved RIP exists**, and why overflowing a buffer can overwrite it, ret2win feels almost magical.

In this article, we'll build the concept from the ground up and understand:

* What a buffer is
* How the stack grows
* What a stack frame contains
* What Saved RBP and Saved RIP are
* Why a buffer overflow can overwrite Saved RIP
* How RIP controls execution
* What ret2win means
* How to calculate the offset
* How to redirect execution to `win()`
* How developers prevent this vulnerability

---

# What Is A Buffer?

A buffer is simply a region of memory used to temporarily store data.

Example:

```c
char buffer[64];
```

This creates a buffer capable of storing:

```text
64 bytes
```

The program might then read user input into it:

```c
read(0, buffer, 64);
```

The important rule is:

```text
Buffer size = 64 bytes
Maximum input = 64 bytes
```

Everything is fine.

---

# What Is A Buffer Overflow?

A Buffer Overflow happens when a program writes more data than the buffer was designed to hold.

For example:

```c
char buffer[64];

read(0, buffer, 256);
```

The buffer can hold:

```text
64 bytes
```

but the program allows:

```text
256 bytes
```

This means the attacker can write beyond the boundaries of `buffer`.

Conceptually:

```text
Input
  │
  ▼
┌──────────────────┐
│     buffer       │
│     64 bytes     │
└──────────────────┘
         │
         ▼
    More input
         │
         ▼
 Data outside buffer
```

This is the fundamental vulnerability.

---

# How Does The Stack Work?

On x86-64 systems, the stack normally grows toward **lower memory addresses**.

```text
Higher addresses
       ↑

       Stack frame

       ↓
Lower addresses
```

However, this does **not** mean that writing more bytes into a buffer moves toward lower addresses.

The stack growth direction and the direction in which consecutive bytes are written are two different concepts.

For a typical vulnerable function:

```c
void vulnerable() {
    char buffer[64];

    read(0, buffer, 256);
}
```

the simplified stack layout can look like:

```text
Higher memory addresses
        ↑

┌──────────────────────┐
│      Saved RIP       │
├──────────────────────┤
│      Saved RBP       │
├──────────────────────┤
│                      │
│      buffer[64]      │
│                      │
└──────────────────────┘
        ↓

Lower memory addresses
```

The important relationship is:

```text
buffer
   ↓
Saved RBP
   ↓
Saved RIP
```

The `buffer` is at a lower address than the Saved RBP and Saved RIP in this typical stack frame.

---

# What Is Saved RBP?

`RBP` is commonly used as the frame pointer.

When a function starts, a typical function prologue looks like:

```asm
push rbp
mov  rbp, rsp
```

The previous value of `RBP` is saved on the stack.

That value is called:

```text
Saved RBP
```

Simplified:

```text
┌──────────────────┐
│    Saved RIP     │
├──────────────────┤
│    Saved RBP     │
├──────────────────┤
│    buffer        │
└──────────────────┘
```

For a basic ret2win challenge, Saved RBP usually isn't our final target.

The interesting target is:

```text
Saved RIP
```

---

# What Is RIP?

`RIP` is the x86-64 **instruction pointer**.

It contains the address of the next instruction the CPU should execute.

For example:

```text
RIP = 0x401166
```

means that execution continues at:

```text
0x401166
```

This makes RIP extremely important.

If an attacker can control RIP:

```text
Attacker
   │
   ▼
Control RIP
   │
   ▼
Control execution
```

This is called:

```text
Control Flow Hijacking
```

---

# What Is Saved RIP?

When a function calls another function, the CPU needs to remember where it should return afterward.

For example:

```c
main()
  │
  └──> vulnerable()
```

When `vulnerable()` eventually finishes, execution should return to `main()`.

The return address is stored on the stack.

Conceptually:

```text
┌──────────────────┐
│    Saved RIP     │ ← Return address
├──────────────────┤
│    Saved RBP     │
├──────────────────┤
│    buffer[64]    │
└──────────────────┘
```

When the function executes:

```asm
ret
```

the CPU uses the value at the top of the stack as the next instruction address.

So:

```text
ret
 ↓
Saved RIP
 ↓
RIP
 ↓
Continue execution
```

This is why controlling Saved RIP is so powerful.

---

# Why Can The Buffer Reach Saved RIP?

This is the most important part.

Suppose:

```text
buffer = 64 bytes
```

and memory looks like:

```text
Higher addresses
        ↑

┌──────────────────┐
│    Saved RIP     │
├──────────────────┤
│    Saved RBP     │
├──────────────────┤
│    buffer        │
└──────────────────┘

        ↓
Lower addresses
```

When the program writes data into the buffer, consecutive bytes are written to consecutive memory addresses.

For example:

```text
buffer starts at:

0x1000
```

Then:

```text
buffer[0] → 0x1000
buffer[1] → 0x1001
buffer[2] → 0x1002
...
```

Therefore, if the attacker writes more than 64 bytes, the extra bytes continue into the memory immediately following the buffer.

Conceptually:

```text
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
BBBBBBBB
CCCCCCCC
```

becomes:

```text
┌──────────────────┐
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │ ← buffer
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
├──────────────────┤
│ BBBBBBBB         │ ← Saved RBP
├──────────────────┤
│ CCCCCCCC         │ ← Saved RIP
└──────────────────┘
```

The overflow didn't "move the stack downward."

Instead:

```text
Stack frame was already created
            ↓
Buffer already has an address
            ↓
Program writes too much data
            ↓
Writing continues into higher addresses
            ↓
Saved RBP overwritten
            ↓
Saved RIP overwritten
```

---

# The Offset To Saved RIP

Suppose our stack layout is:

```text
buffer = 64 bytes
Saved RBP = 8 bytes
Saved RIP = 8 bytes
```

To reach Saved RIP:

```text
64 bytes
+
8 bytes Saved RBP
=
72 bytes
```

Therefore:

```text
Offset = 72
```

The payload conceptually becomes:

```text
"A" * 72
+
WIN_ADDRESS
```

The first:

```text
64 bytes
```

fill the buffer.

The next:

```text
8 bytes
```

overwrite Saved RBP.

The next:

```text
8 bytes
```

become the new Saved RIP.

---

# What Is ret2win?

`ret2win` means:

```text
Return To win()
```

The challenge contains a function such as:

```c
void win(void) {
    puts("FLAG{buffer_overflow_ret2win}");
}
```

Normally, the program never calls `win()`.

The attacker changes Saved RIP so that when the vulnerable function executes:

```asm
ret
```

execution goes to:

```text
win()
```

instead of returning normally.

The entire attack becomes:

```text
Buffer Overflow
      ↓
Overwrite Saved RBP
      ↓
Overwrite Saved RIP
      ↓
Control RIP
      ↓
ret
      ↓
win()
      ↓
FLAG
```

---

# Vulnerable Example

Our vulnerable function looks like:

```c
void vulnerable(void) {
    char buffer[64];

    printf("Input: ");

    read(STDIN_FILENO, buffer, 256);

    puts("Done.");
}
```

The problem is:

```c
char buffer[64];
```

but:

```c
read(..., buffer, 256);
```

allows 256 bytes to be written.

The application assumes:

```text
64 bytes
```

while the attacker can provide:

```text
256 bytes
```

---

# Finding win()

The binary contains:

```c
void win(void) {
    puts("FLAG{buffer_overflow_ret2win}");
}
```

We can find its address using:

```bash
nm vuln | grep ' win$'
```

Example:

```text
0000000000401166 T win
```

Therefore:

```text
win() = 0x401166
```

The exact address depends on the binary.

---

# Finding The Offset

We first determine how many bytes are required to reach Saved RIP.

For our simple stack layout:

```text
buffer
   │
   │ 64 bytes
   ↓
Saved RBP
   │
   │ 8 bytes
   ↓
Saved RIP
```

Therefore:

```text
64 + 8 = 72
```

So:

```text
Saved RIP offset = 72
```

In real exploitation, we normally verify the offset rather than blindly assuming it.

For example, GDB can be used to inspect the crash:

```bash
gdb ./vuln
```

Then:

```gdb
run
```

After the crash:

```gdb
info registers
```

and:

```gdb
x/20gx $rsp
```

These allow us to inspect the stack and determine whether our input reached the saved return address.

---

# Constructing The Payload

Once we know:

```text
Offset = 72
win()  = 0x401166
```

we need:

```text
72 bytes of padding
+
address of win()
```

On x86-64, addresses are normally represented in little-endian byte order when placed in memory.

Python can construct the payload:

```python
import struct

payload = b"A" * 72
payload += struct.pack("<Q", 0x401166)
```

Then:

```bash
python3 exploit.py | ./vuln
```

The result is:

```text
Buffer Overflow
      ↓
72 bytes
      ↓
Saved RIP overwritten
      ↓
RIP = win()
      ↓
win()
      ↓
FLAG
```

---

# Why Does ret Use Our Address?

At the end of the vulnerable function, the CPU executes:

```asm
ret
```

Conceptually, `ret` does:

```text
Take address from stack
        ↓
Put it into RIP
        ↓
Continue execution there
```

Before exploitation:

```text
Saved RIP = address inside main()
```

So:

```text
ret
 ↓
main()
```

After exploitation:

```text
Saved RIP = address of win()
```

So:

```text
ret
 ↓
win()
```

This is the fundamental idea behind ret2win.

---

# Complete Attack Flow

```text
                User Input
                    │
                    ▼
             buffer[64]
                    │
                    ▼
             Buffer Overflow
                    │
                    ▼
             Saved RBP
                    │
                    ▼
             Saved RIP
                    │
                    ▼
              Control RIP
                    │
                    ▼
                  ret
                    │
                    ▼
                 win()
                    │
                    ▼
                  FLAG
```

---

# Important Mental Model

Do not memorize:

```text
"A" * 72
```

Instead understand why it is 72.

```text
64 bytes
   │
   ├── buffer
   │
   └── 8 bytes Saved RBP
            │
            ▼
        Saved RIP
```

Therefore:

```text
64 + 8 = 72
```

The payload isn't magic.

It is simply matching the memory layout.

---

# What Happens If We Send Too Little?

Suppose:

```text
"A" * 40
```

The input stays inside the buffer.

```text
┌──────────────────┐
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAA         │
│                  │
└──────────────────┘
│ Saved RBP        │
├──────────────────┤
│ Saved RIP        │
└──────────────────┘
```

No Saved RIP control.

---

# What Happens At 64 Bytes?

```text
"A" * 64
```

The buffer is completely filled:

```text
┌──────────────────┐
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
├──────────────────┤
│ Saved RBP        │
├──────────────────┤
│ Saved RIP        │
└──────────────────┘
```

Still no Saved RIP overwrite.

---

# What Happens At 72 Bytes?

```text
"A" * 72
```

Now:

```text
64 bytes → buffer
8 bytes  → Saved RBP
```

The Saved RIP is next.

---

# What Happens At 80 Bytes?

```text
"A" * 72 + "B" * 8
```

Conceptually:

```text
┌──────────────────┐
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
│ AAAAAAAAAAAAAAAA │
├──────────────────┤
│ AAAAAAAA         │ ← Saved RBP
├──────────────────┤
│ BBBBBBBB         │ ← Saved RIP
└──────────────────┘
```

Now the attacker controls the return address.

---

# Control Flow Hijacking

Once Saved RIP is controlled:

```text
Saved RIP
    │
    ▼
Attacker-controlled address
    │
    ▼
CPU executes attacker-selected code location
```

This is called:

```text
Control Flow Hijacking
```

In our lab, we don't need to inject shellcode.

We simply redirect execution to code that already exists:

```text
win()
```

Therefore:

```text
ret2win
```

is one of the simplest examples of control-flow hijacking.

---

# Why ret2win Doesn't Need Shellcode

We already have:

```c
void win(void) {
    puts("FLAG{buffer_overflow_ret2win}");
}
```

The function is already inside the executable.

Therefore, instead of injecting new code:

```text
Attacker
   ↓
Inject shellcode
```

we do:

```text
Attacker
   ↓
Reuse existing code
   ↓
win()
```

This idea leads to more advanced exploitation techniques such as:

```text
ret2win
   ↓
ret2libc
   ↓
ROP
   ↓
Advanced Control Flow Hijacking
```

---

# How To Identify A ret2win Challenge

When looking at a binary, ask:

```text
1. Is there a memory corruption vulnerability?
              ↓
2. Can I overwrite Saved RIP?
              ↓
3. Is there a useful function already in the binary?
              ↓
4. Does that function print a flag or give useful behavior?
              ↓
5. Can I redirect RIP to that function?
```

If the answer is yes:

```text
ret2win
```

is likely the intended technique.

---

# Common Mistakes

## Mistake 1 — Thinking Stack Growth Equals Input Direction

The stack grows toward lower addresses:

```text
Stack growth
     ↓
Lower addresses
```

But when writing sequential bytes into a buffer:

```text
buffer[0]
buffer[1]
buffer[2]
...
```

addresses increase:

```text
0x1000
0x1001
0x1002
...
```

Therefore the overflow can move from the buffer toward Saved RBP and Saved RIP.

---

## Mistake 2 — Assuming The Offset Is Always 72

Our example uses:

```text
64-byte buffer
+
8-byte Saved RBP
=
72
```

But real binaries can have:

* Different buffer sizes
* Compiler-generated padding
* Different stack layouts
* Stack alignment
* Different compiler optimizations

Therefore:

```text
Never blindly assume the offset.
```

Determine it from the actual binary.

---

## Mistake 3 — Forgetting Little Endian

On x86-64, if:

```text
win() = 0x401166
```

the bytes placed in memory are represented little-endian:

```text
66 11 40 00 00 00 00 00
```

Python handles this using:

```python
struct.pack("<Q", win_address)
```

where:

```text
<
```

means little-endian.

and:

```text
Q
```

means an unsigned 64-bit integer.

---

# Defenses

The vulnerability exists because the program allows more data to be written than the buffer can hold.

Instead of:

```c
char buffer[64];

read(0, buffer, 256);
```

use a bounded operation:

```c
char buffer[64];

read(0, buffer, sizeof(buffer) - 1);
```

The program should never allow user-controlled input to exceed the destination buffer.

---

# Compiler Protections

Modern systems also provide several protections against stack-based exploitation.

Common protections include:

```text
Stack Canaries
NX / DEP
PIE
ASLR
RELRO
```

Check a binary using:

```bash
checksec --file=./vuln
```

A simple educational ret2win binary may intentionally disable some protections so that the fundamental concept is easier to understand.

Real-world exploitation is often more complicated because these protections must be considered.

---

# Secure Mental Model

The most important concepts are:

```text
Stack
  ↓
Stack frame
  ↓
Buffer
  ↓
Saved RBP
  ↓
Saved RIP
  ↓
ret
  ↓
RIP
```

The vulnerability changes this:

```text
Normal:

Saved RIP
    ↓
Return to main()
```

into:

```text
Exploited:

Saved RIP
    ↓
Address of win()
    ↓
win()
    ↓
FLAG
```

---

# Quick Summary

## Buffer Overflow

Writing more data than a buffer can hold.

```text
64-byte buffer
      +
256-byte input
      =
Buffer Overflow
```

## Saved RIP

The saved return address used when the function returns.

```text
ret
 ↓
Saved RIP
 ↓
RIP
```

## Control Flow Hijacking

Controlling Saved RIP allows us to choose where execution continues.

```text
Saved RIP
    ↓
Attacker-controlled address
    ↓
Controlled execution
```

## ret2win

Redirecting execution to an existing `win()` function.

```text
Buffer Overflow
      ↓
Saved RIP Overwrite
      ↓
Control RIP
      ↓
ret
      ↓
win()
      ↓
FLAG
```

## Core Formula

For our simple lab:

```text
Buffer
  = 64 bytes

Saved RBP
  = 8 bytes

Offset to Saved RIP
  = 64 + 8
  = 72 bytes
```

Payload:

```text
"A" * 72 + address(win)
```

The important lesson is not the payload.

The important lesson is understanding the chain:

```text
Buffer Overflow
      ↓
Memory Corruption
      ↓
Saved RIP Overwrite
      ↓
Control Flow Hijacking
      ↓
ret2win
      ↓
win()
      ↓
FLAG
```
