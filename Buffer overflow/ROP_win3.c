#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int win1 = 0;
int win2 = 0;
int win3 = 0;

void win(void) {
    if (win1 && win2 && win3) {
        printf("\n================================\n");
        printf("        RET2WIN SUCCESS!\n");
        printf("================================\n");
        printf("FLAG{buffer_overflow_three_wins}\n");
        printf("================================\n\n");

        exit(0);
    }

    puts("\nNot all conditions are satisfied!");
    printf("win1 = %d\n", win1);
    printf("win2 = %d\n", win2);
    printf("win3 = %d\n", win3);
}

void vulnerable(void) {
    char buffer[64];

    puts("================================");
    puts("     Ret2Win Three Conditions");
    puts("================================");
    puts("Your goal is to make:");
    puts("  win1 = 1");
    puts("  win2 = 1");
    puts("  win3 = 1");
    puts("");
    puts("Then redirect execution to win().");
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
