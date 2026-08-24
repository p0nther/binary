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
    puts("       Ret2Win Fixed Lab");
    puts("================================");
    printf("Input: ");

    fflush(stdout);

    if (read(STDIN_FILENO, buffer, sizeof(buffer) - 1) < 0) {
        perror("read");
        exit(1);
    }

    buffer[sizeof(buffer) - 1] = '\0';

    puts("\nDone.");
}

int main(void) {
    setbuf(stdout, NULL);

    vulnerable();

    puts("Returned normally.");
    return 0;
}
