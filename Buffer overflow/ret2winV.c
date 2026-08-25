#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void win(void) {
    puts("\n================================");
    puts("        RET2WIN SUCCESS!");
    puts("================================");
    puts("FLAG{buffer_overflow_ret2win}");
    puts("================================\n");

    exit(0);
}

void vulnerable(void) {
    char buffer[64];

    puts("================================");
    puts("       Ret2Win Local Lab");
    puts("================================");
    puts("Overflow the buffer and redirect");
    puts("execution to win().");
    puts("");
    printf("Input: ");

    fflush(stdout);

    read(STDIN_FILENO, buffer, 256);

    puts("\nDone.");
}

int main(void) {
    setbuf(stdout, NULL);

    vulnerable();

    puts("Returned normally.");
    return 0;
}
