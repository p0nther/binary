# Buffer Overflow — Complete Notes

When many beginners first encounter Buffer Overflow, they immediately start memorizing things like:

```text
"A" * 64
"A" * 72 + win_address
cyclic patterns
```

and start trying random payloads until the program crashes.

But without understanding **how memory is organized, how stack frames work, and what happens when a program writes beyond a buffer**, Buffer Overflow can feel confusing.

In this article, we'll build the concept from the ground up and understand:

* What a buffer is
* What a Buffer Overflow is
* How the stack works
* How stack frames are organized
* What Saved RBP is
* What Saved RIP is
* Why overflowing a buffer can overwrite Saved RIP
* What Control Flow Hijacking means
* What ret2win is
* How attackers calculate the offset
* How modern protections make exploitation harder
* How developers prevent Buffer Overflow vulnerabilities

---

# What Is A Buffer?

A **buffer** is a region of memory used to temporarily store data.

For example:

```c
char buffer[64];
```

creates a buffer capable of storing:

```text
64 bytes
```

The important idea is that a buffer has a **fixed amount of memory**.

Conceptually:

```text
┌──────────────────────────────┐
│                              │
│          buffer              │
│          64 bytes            │
│                              │
└──────────────────────────────┘
```

As long as the program writes no more than 64 bytes into this buffer, everything is fine.

---

# What Is A Buffer Overflow?

A **Buffer Overflow** occurs when a program writes more data into a buffer than the buffer was designed to hold.

For example:

```c
char buffer[64];

read(0, buffer, 256);
```

The program allocated:

```text
64 bytes
```

but allows:

```text
256 bytes
```

to be written.

The problem is:

```text
Buffer capacity
      ↓
   64 bytes

Input allowed
      ↓
  256 bytes
```

The additional data can overwrite memory belonging to other objects.

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
Memory outside buffer
```

This is the fundamental vulnerability.

---

# Why Is Buffer Overflow Dangerous?

A Buffer Overflow is not dangerous simply because some bytes were written outside a buffer.

The real danger depends on **what exists next to the buffer in memory**.

The overwritten data might be:

* Another variable
* A pointer
* A structure field
* A function pointer
* Stack metadata
* A saved return address

If security-sensitive data is corrupted, the attacker may be able to change the program's behavior.

In the most interesting cases, the attacker can corrupt **control-flow data**.

That leads to:

```text
Buffer Overflow
      ↓
Memory Corruption
      ↓
Control Flow Hijacking
```

---

# Where Does The Buffer Exist?

A buffer can exist in different memory regions depending on how it is created.

For example:

```c
char buffer[64];
```

inside a function normally creates a local buffer on the **stack**.

While:

```c
char *buffer = malloc(64);
```

creates dynamically allocated memory on the **heap**.

Therefore, "Buffer Overflow" is a general memory corruption vulnerability.

This article focuses primarily on:

```text
Stack-based Buffer Overflow
```

because it provides the foundation for understanding Saved RIP and ret2win.

---

# What Is The Stack?

The **stack** is a region of memory used by programs for things such as:

* Function calls
* Local variables
* Saved registers
* Return addresses
* Temporary data

On common x86-64 systems, the stack generally grows toward **lower memory addresses**.

Conceptually:

```text
Higher addresses
       ↑

       Stack

       ↓
Lower addresses
```

The phrase:

```text
Stack grows downward
```

means that when the program allocates more stack space, the stack pointer moves toward lower addresses.

It does **not** mean that every write performed inside a stack buffer moves toward lower addresses.

That distinction is extremely important.

---

# What Is A Stack Frame?

When a function executes, it needs space for its local state.

This creates what is commonly called a:

```text
Stack Frame
```

A simplified stack frame might look like:

```text
Higher memory addresses
        ↑

┌──────────────────────┐
│      Saved RIP       │
├──────────────────────┤
│      Saved RBP       │
├──────────────────────┤
│                      │
│      Local buffer    │
│                      │
└──────────────────────┘

        ↓
Lower memory addresses
```

The exact layout is compiler- and architecture-dependent, but this simplified model is extremely useful when learning stack-based exploitation.

---

# What Is RBP?

`RBP` is a CPU register commonly used as a **frame pointer**.

A traditional function prologue may look like:

```asm
push rbp
mov  rbp, rsp
```

The previous value of `RBP` is saved on the stack.

This is called:

```text
Saved RBP
```

A simplified layout is:

```text
┌──────────────────┐
│    Saved RIP     │
├──────────────────┤
│    Saved RBP     │
├──────────────────┤
│    Local buffer  │
└──────────────────┘
```

Saved RBP can sometimes be corrupted during a Buffer Overflow, but in a basic ret2win exploit, it is usually not the main target.

---

# What Is RIP?

`RIP` is the x86-64 **instruction pointer**.

It tells the CPU where execution should continue.

For example:

```text
RIP = 0x401234
```

means that the CPU will execute instructions beginning at that address.

Therefore, controlling RIP means controlling the program's execution location.

This is why attackers are interested in overwriting the saved return address.

---

# What Is The Saved RIP?

When one function calls another function, the program needs to remember where execution should return afterward.

That return address is stored on the stack.

For example:

```text
main()
  │
  └──> function()
```

The function eventually returns to `main()`.

Conceptually:

```text
┌──────────────────┐
│    Saved RIP     │ ← Return address
├──────────────────┤
│    Saved RBP     │
├──────────────────┤
│    buffer        │
└──────────────────┘
```

When the function executes:

```asm
ret
```

the CPU uses the saved return address to continue execution.

Conceptually:

```text
ret
 ↓
Saved RIP
 ↓
RIP
 ↓
Continue execution
```

This makes Saved RIP a particularly valuable target.

---

# Why Can A Buffer Overflow Reach Saved RIP?

This is where the memory layout becomes important.

Suppose the simplified stack frame is:

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

The buffer has a starting memory address.

If the program writes sequential bytes into the buffer, the bytes occupy consecutive addresses.

For example, if the buffer starts at:

```text
0x1000
```

then:

```text
buffer[0] → 0x1000
buffer[1] → 0x1001
buffer[2] → 0x1002
buffer[3] → 0x1003
```

and so on.

Therefore, if the program continues writing after the end of the buffer, the writes can reach the memory located immediately after it.

Conceptually:

```text
┌──────────────────┐
│     buffer       │
├──────────────────┤
│    Saved RBP     │
├──────────────────┤
│    Saved RIP     │
└──────────────────┘
```

becomes:

```text
┌──────────────────┐
│     attacker     │
│      input       │
├──────────────────┤
│ overwritten RBP  │
├──────────────────┤
│ overwritten RIP  │
└──────────────────┘
```

The important point is:

> The stack grows downward, but sequential writes to an array increase the memory address.

There is no contradiction between these two facts.

---

# Understanding The Overflow Direction

This is one of the most common sources of confusion.

There are two different concepts:

### Stack Growth

When stack space is allocated:

```text
Stack
  ↓
Lower addresses
```

### Sequential Buffer Writes

When data is written to:

```c
buffer[i]
```

and `i` increases:

```text
buffer[0]
   ↓
buffer[1]
   ↓
buffer[2]
   ↓
...
```

the memory addresses increase.

So the simplified relationship is:

```text
Higher addresses
       ↑

   Saved RIP
       ↑
   Saved RBP
       ↑
    buffer
       ↑
      RSP

       ↓
Lower addresses
```

The overflow moves from the buffer toward the higher-addressed data above it.

---

# Control Flow Hijacking

If an attacker successfully overwrites Saved RIP, they may be able to choose where the program executes after the function returns.

Normally:

```text
Function
   ↓
ret
   ↓
Saved RIP
   ↓
Normal caller
```

After exploitation:

```text
Function
   ↓
ret
   ↓
Attacker-controlled Saved RIP
   ↓
Chosen code location
```

This is called:

```text
Control Flow Hijacking
```

It is one of the most important concepts in binary exploitation.

---

# What Is ret2win?

**ret2win** means:

```text
Return To win()
```

The program already contains a useful function, commonly called something like:

```c
void win(void) {
    puts("FLAG{...}");
}
```

The attacker does not need to inject new code.

Instead, they overwrite the saved return address with the address of the existing `win()` function.

The flow becomes:

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

This is why ret2win is such an important beginner exploitation technique.

It teaches the fundamental concept of:

```text
"I don't need to execute code I injected.
I can redirect execution to code that already exists."
```

---

# Understanding The Offset

The **offset** is the number of bytes required to reach the saved return address.

For a simplified example:

```text
buffer = 64 bytes
Saved RBP = 8 bytes
```

Then:

```text
64 + 8 = 72
```

So the saved RIP begins after:

```text
72 bytes
```

Conceptually:

```text
┌────────────────────────┐
│       64 bytes         │ ← buffer
├────────────────────────┤
│        8 bytes         │ ← Saved RBP
├────────────────────────┤
│        Saved RIP       │ ← target
└────────────────────────┘
```

Therefore:

```text
Offset to Saved RIP = 72
```

However, this is **not a universal rule**.

Real binaries may contain:

* Compiler-generated padding
* Different local-variable layouts
* Different stack alignment
* Optimizations
* Different compiler behavior
* Omitted frame pointers

Therefore:

> The offset must be determined from the actual binary.

---

# Why The Offset Is Important

Suppose an attacker sends:

```text
40 bytes
```

The input may remain entirely inside the buffer.

No Saved RIP control.

If they send:

```text
64 bytes
```

the buffer is filled, but Saved RIP may still be untouched.

If they send enough bytes to pass:

```text
buffer
+
Saved RBP
```

then the next bytes can overwrite Saved RIP.

This is why exploitation often starts with:

```text
Find the exact offset
```

before constructing the final payload.

---

# The General ret2win Payload Structure

Once the offset and target address are known, the conceptual payload is:

```text
Padding
   +
Target Address
```

For example:

```text
"A" * OFFSET + address_of_win
```

The padding exists only to reach the Saved RIP.

The target address replaces the original return address.

So the payload is really saying:

```text
"Fill everything until Saved RIP,
then replace Saved RIP with the address I want."
```

---

# Why Little Endian Matters

On x86-64 systems, multi-byte values are commonly stored in **little-endian** order.

Suppose:

```text
win() = 0x401166
```

The 64-bit representation is stored as:

```text
66 11 40 00 00 00 00 00
```

This is why exploitation tools commonly use something equivalent to:

```python
struct.pack("<Q", address)
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

represents an unsigned 64-bit value.

Understanding endianness is important because the CPU interprets the bytes as an address.

---

# From Buffer Overflow To ret2win

The entire concept can be summarized as:

```text
              Buffer
                 │
                 ▼
          Too much input
                 │
                 ▼
        Buffer Overflow
                 │
                 ▼
        Memory Corruption
                 │
                 ▼
        Saved RIP Overwrite
                 │
                 ▼
        Control Flow Hijacking
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

Every step follows directly from the previous one.

---

# Common Misconceptions

## "The stack grows downward, so overflow should go downward."

Not necessarily.

These are different concepts.

```text
Stack allocation:
        ↓
Lower addresses
```

while sequential writes into an array are:

```text
buffer[0]
buffer[1]
buffer[2]
...
        ↓
Higher addresses
```

That is why a stack buffer can overwrite data located at higher addresses.

---

## "The Buffer Overflow automatically controls RIP."

No.

There are several conditions that must be satisfied.

The attacker needs:

```text
Buffer Overflow
      ↓
Reach Saved RIP
      ↓
Control its value
      ↓
Choose a useful target
```

A crash alone does not mean successful control-flow hijacking.

---

## "Saved RBP is the target."

Usually not in a basic ret2win.

The interesting target is:

```text
Saved RIP
```

because it determines where execution continues after `ret`.

---

## "The offset is always 72."

No.

`72` is only an example for a particular stack layout:

```text
64-byte buffer
+
8-byte Saved RBP
=
72
```

Different binaries can have different layouts.

---

# Impact

The impact of a Buffer Overflow depends on what the attacker can corrupt.

Possible consequences include:

* Application crash
* Denial of Service
* Memory corruption
* Control Flow Hijacking
* Arbitrary code execution
* Privilege escalation
* Information disclosure
* Compromise of the affected process

A simple ret2win challenge demonstrates only one controlled outcome:

```text
Buffer Overflow
      ↓
Control Flow Hijacking
      ↓
Existing Function
```

Real-world exploitation can be considerably more complex.

---

# Modern Protections

Modern operating systems and compilers implement protections specifically designed to make exploitation harder.

Common protections include:

## Stack Canaries

A secret value is placed near control-flow data.

If a Buffer Overflow modifies the canary, the program detects the corruption before returning.

Conceptually:

```text
buffer
   ↓
canary
   ↓
Saved RBP
   ↓
Saved RIP
```

An attacker who overwrites through the canary may trigger a protection failure.

---

## NX / DEP

Marks memory regions such as the stack as non-executable.

This makes traditional stack-based shellcode execution much harder.

The attacker may instead need to reuse existing executable code.

This is one reason techniques such as:

```text
ret2libc
ROP
```

became important.

---

## ASLR

**Address Space Layout Randomization** changes memory locations between executions.

This makes it harder to predict addresses such as:

```text
libc
stack
heap
shared libraries
```

---

## PIE

**Position Independent Executables** allow the main executable itself to be relocated.

Without PIE, code addresses in the main executable may remain predictable.

With PIE:

```text
Program address
      ↓
Randomized
```

which can complicate ret2win-style exploitation.

---

## RELRO

**Relocation Read-Only** protections harden certain ELF relocation structures.

It is particularly relevant to attacks involving structures such as the GOT.

---

# How Developers Prevent Buffer Overflow

The fundamental defense is simple:

> Never allow more data to be written than the destination can hold.

Instead of an unsafe operation that allows arbitrary amounts of data:

```c
read(fd, buffer, 256);
```

when:

```c
char buffer[64];
```

use a correctly bounded size:

```c
read(fd, buffer, sizeof(buffer));
```

Other defensive practices include:

* Bounds checking
* Safe memory-handling APIs
* Compiler hardening
* Stack canaries
* ASLR
* PIE
* NX
* Memory-safe languages where appropriate
* Fuzz testing
* Static analysis
* Code review

---

# Vulnerability → Exploitation Chain

The complete conceptual chain is:

```text
Buffer
   ↓
Too much input
   ↓
Buffer Overflow
   ↓
Memory Corruption
   ↓
Overwrite Saved RBP
   ↓
Overwrite Saved RIP
   ↓
Control RIP
   ↓
Control Flow Hijacking
   ↓
ret2win
   ↓
Existing win() function
```

The key transition is:

```text
Memory Corruption
       ↓
Control Flow Corruption
```

Once an attacker can reliably control a return address, the vulnerability becomes much more powerful than a simple crash.

---

# Quick Summary

### Buffer Overflow

Writing more data than a buffer can hold.

```text
Buffer capacity
      ↓
64 bytes

Input
      ↓
More than 64 bytes
```

### Stack

A memory region used for function execution and local state.

```text
Stack growth
     ↓
Lower addresses
```

### Saved RBP

A saved frame-pointer value belonging to the previous stack frame.

### Saved RIP

The saved return address used when the function returns.

```text
ret
 ↓
Saved RIP
 ↓
RIP
```

### Control Flow Hijacking

Controlling the saved return address to change where execution continues.

### ret2win

Redirecting execution to an existing `win()` function.

```text
Buffer Overflow
      ↓
Saved RIP Overwrite
      ↓
Control Flow Hijacking
      ↓
ret
      ↓
win()
```

### Core Mental Model

```text
Higher addresses
       ↑

┌──────────────────┐
│    Saved RIP     │ ← control-flow target
├──────────────────┤
│    Saved RBP     │
├──────────────────┤
│      Buffer      │ ← attacker-controlled input
└──────────────────┘

       ↓
Lower addresses

Stack grows ↓
Sequential buffer writes move toward ↑
```

The most important idea is:

> **A Buffer Overflow becomes especially powerful when the attacker can overwrite control-flow data such as a saved return address. Once Saved RIP is controlled, execution can potentially be redirected to attacker-chosen code or existing functions.**
