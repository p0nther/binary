CC = gcc

CFLAGS = -g -O0 \
         -fno-stack-protector \
         -no-pie \
         -Wl,-z,norelro

all: vuln fix

vuln: appVuln.c
	$(CC) $(CFLAGS) appVuln.c -o vuln

fix: appFix.c
	$(CC) -g -O0 appFix.c -o fix

clean:
	rm -f vuln fix
